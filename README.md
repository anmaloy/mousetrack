# mousetrack
Tracks the movement of mice from video and detects various behaviors.

About
----

Mousetrack is an OpenCV-based program that allows for the tracking and assessment of mouse motion in video footage. It is specifically designed for use in stretching/writhing and rearing assays.

Mousetrack was developed as part of an undergraduate research project aimed at developing foundations for more translatable models of pain in mice, the paper detailing the project can be found [here]() 

Mousetrack makes use of modified and unmodified code from the [vivekhsridhar/tracktor](https://github.com/vivekhsridhar/tracktor) repository for the actual tracking process.

Instructions
----

To use mousetrack, you will need a Python installation and the following packages:

  * cv2 
  * glob
  * imageio
  * matplotlib
  * numpy
  * os
  * pandas
  * scipy
  * sklearn
  * sys
  * time
  
Instructions for setting up a Python environment on Windows can be found [here](https://docs.python.org/3/using/windows.html)

Once you have the necessary dependencies, download this repository to your desired location. Copy the videos you want to track and analyze into the videos/in directory and run mousetrack.py. Each video will be displayed in turn.

You will first need to select the start time for each video. The video will open in a window and begin playing. When you want the video assessment (i.e. when the assay begins) to start, press ESC. The frame you selected will open in a separate window.

Next, you will need to correct for any crookedness in the video. Find a straight line in the image and double-click on one side of it, followed by pressing 'a'. Repeat on the other side and press ESC to close the image. This will provide the coordinates necessary to correct for a video that wasn't recorded straight, which may affect the assessment. If the video is straight to begin with, simply press ESC and the final window will open.

Lastly, you have to select the areas of interest for the program to assess. Normally, this would be the area of the cage. Hold the left-click button and drag a box over each relevant area. Press ENTER after each box is drawn to record it.

After completing these steps, wait until the program is finished running. The results will be saved in the results directory. The directory will contain a chart for each stretching and rearing depicting the counted events and a final results.csv file, which contains the total rearing and stretching count for each mouse."
