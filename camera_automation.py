import cv2
from PIL import Image
import time
import datetime

import numpy as np

import pypylon.pylon as py


def main():
    get_images(max_frames=100, time_frame=100)


def get_images(max_frames = 100, time_frame=100, adjust_exposure=True):
    tlf = py.TlFactory.GetInstance()
    try:
        cam = py.InstantCamera(tlf.CreateFirstDevice()) # or py.InstantCamera(tlf.CreateDevice(devices[0]))
        cam.Open()

        # Camera settings
        cam.ExposureTime = cam.ExposureTime.Min # it will increase by itself
        cam.PixelFormat = "Mono12p" # Highest available we can change

        # Capture Strategy
        cam.StartGrabbing(py.GrabStrategy_OneByOne)

        if adjust_exposure:
            while True:
                try:
                    convergence_rate = input(f"Here you can set your convergence rate between 0.01 and 1."
                              f"\nYou can quit by pressing: 'q', 'quit', 'e', 'exit'."
                              f"\nConvergence rate (suggested value = {0.2}): ")
                    if 0.01 <= float(convergence_rate) <= 1:  # Check for valid intensity range
                        break
                    elif convergence_rate.lower() in ['q', 'quit', 'e', 'exit']:
                        convergence_rate = 0
                        print("Exiting exposure adjustment.")
                        break
                    else:
                        print("Invalid a value. Please enter a value between 0.01 and 1.")
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")

            print(f'Starting to adjust exposure time\n...\n...')
            if convergence_rate:
                set_exposure_time(cam, time_frame, float(convergence_rate))
            else:
                set_exposure_time(cam, time_frame)


        i = 0
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        print(f'Starting to acquire\n...\n...')
        t0 = time.time()

        while cam.IsGrabbing():
            grab = cam.RetrieveResult(time_frame, py.TimeoutHandling_Return)
            if grab.GrabSucceeded():
                image_data = grab.GetArray()
                image = Image.fromarray(image_data)
                image.save(f'{current_date}_{i}.png')
                i += 1
            if i == max_frames:
                break

        print(f'Done!\nAcquired {i} frames in {time.time()-t0:.0f} seconds')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if cam:
            cam.Close()


def set_exposure_time(cam, time_frame, convergence_rate=0.2):
    default_intensity = 128
    while True:
        try:
            desired_intensity = input(f"Here you can set your desired intensity between 0 and 255."
                                      f"\n You can quit by pressing: 'q', 'quit', 'e', 'exit'."
                                      f"Intensity (suggested value = {default_intensity}): .")
            if 0 <= int(desired_intensity) <= 255:  # Check for valid intensity range
                break
            elif desired_intensity.lower() in  ['q', 'quit', 'e','exit']:
                print("Exiting exposure adjustment.")
                break
            else:
                print("Invalid intensity value. Please enter a value between 0 and 255.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    for _ in range(25):
        grab = cam.RetrieveResult(time_frame, py.TimeoutHandling_Return)
        if grab.GrabSucceeded():
            image_data = grab.GetArray()
            image = Image.fromarray(image_data)

            # Convert image to grayscale for easier analysis
            gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)

            # Calculate average pixel intensity
            avg_intensity = np.mean(gray_image)

            # Adjust exposure time based on average intensity
            if avg_intensity < desired_intensity:
                cam.ExposureTime *= 1 + convergence_rate
            elif avg_intensity > desired_intensity:
                cam.ExposureTime *= 1 + convergence_rate

            # Return Exposure Time if the error is 0.05
            if abs(avg_intensity / desired_intensity) <= 0.05:
                break

    print(f'Current Exposure Time: {cam.ExposureTime}')


if __name__ == "__main__":
    main()
