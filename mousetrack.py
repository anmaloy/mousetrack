"""
mousetrack takes a video and processes it before passing it to tracktor.
Once returned it does the analysis of the mouse position to detect rearing and stretching behavior.
"""

import cv2
import glob
import imageio
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from scipy.signal import find_peaks
import sys
import time

import tracktor as tr


class Automate:
    path = 'videos\\in'
    # Dataframe which holds video name and selectROI data
    df = pd.DataFrame(columns=['name', 'startFrame', '0', '1', '2', '3', 'angle', 'file'])
    # Iterator used for distinguishing different cuts of the same video
    out_iter = 0
    # Determines how many frames will be skipped for each one tracked/recorded
    # 1 to record and track every frame, 6 is faster and loses little accuracy
    frame_modulo = 6

    @staticmethod
    def count_frames(video):
        """Returns the number of frames in a video"""
        cap = cv2.VideoCapture(video)
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return length

    @staticmethod
    def select_start(file):
        """Returns the frame at which the video will start tracking"""
        capture = cv2.VideoCapture(file)
        if not capture.isOpened():
            print('Cannot open video')
            sys.exit()

        ok, frame = capture.read()
        if not ok:
            print('Cannot read video')
            sys.exit()
        while True:
            ok, frame = capture.read()
            cv2.putText(frame, "Press esc when time trial starts", (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                        (50, 170, 50), 2)
            cv2.imshow("temp", frame)
            k = cv2.waitKey(1) & 0xff
            if k == 27:
                return int(capture.get(cv2.CAP_PROP_POS_FRAMES))

    @staticmethod
    def clear_files():
        """Deletes the videos and files generated by the program, runs at the beginning and end to prevent clogs"""
        files = glob.glob('videos\\out\\*.mp4')
        for video in files:
            try:
                os.remove(video)
            except OSError as e:
                print("Error: %s : %s" % (video, e.strerror))
        files = glob.glob('processing\\*.csv')
        for file in files:
            try:
                os.remove(file)
            except OSError as e:
                print("Error: %s : %s" % (file, e.strerror))

    @staticmethod
    def get_angle(image):
        """
        Returns the angle necessary to correct a crooked video.
        Double click on one side of the video to create a point and press 'a' to record it.
        Repeat on the other side in a straight line to correct the angle offset as needed.
        """

        def mark(event, x, y, flags, param):
            global point_a, point_b
            if event == cv2.EVENT_LBUTTONDBLCLK:
                cv2.circle(image, (x, y), 5, (255, 0, 0), -1)
                point_a, point_b = x, y

        # initializes lists to store X and Y coordinates of the clicks
        lst_a = []
        lst_b = []
        cv2.namedWindow('image')
        cv2.setMouseCallback('image', mark)
        # Opens image for the duration of marking, esc to close
        while 1:
            cv2.imshow('image', image)
            k = cv2.waitKey(20) & 0xFF
            if k == 27:
                break
            # Commits coordinates of previous click on pressing 'a'
            elif k == ord('a'):
                lst_a.append(point_b)
                lst_b.append(point_a)
        if lst_a and lst_b:
            # Converts the mouse coordinates into size width and height
            w = lst_b[1] - lst_b[0]
            h = lst_a[1] - lst_a[0]
            # Finds the angle of change based on the size of the triangle sides
            angle = round(np.sin(h / w) * (180 / np.pi), 1)
        else:
            angle = 0
        return angle

    @staticmethod
    def rotate_image(image, angle):
        """Rotates each frame according to the get_angle"""
        # Locates the center of the image
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        # Finds rotation matrix
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        # Rotates using an affine transformation
        result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
        return result

    def convert_video(self):
        """"Creates a .mp4 conversion of other video types, saves in the same directory"""
        video_types = ['.webm', '.mkv', '.flv', '.vob', '.ogv', '.ogg', '.drc', '.gif', '.gifv', '.mng',
                       '.avi', '.MTS', '.M2TS', '.mov', '.qt', '.wmv', '.yuv', '.rm', '.rmvb', '.viv', '.asf',
                       '.amv', '.m4p', '.m4v', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m2v', '.svi', '.3gp',
                       '.3g2', '.mxf', '.roq', '.nsv', '.flv', '.f4v', '.f4p', '.f4a', '.f4b']
        for video in glob.glob(self.path):
            new_str = video.split('.', 1)[0]
            if new_str in video_types:
                dest = new_str + '.mp4'
                reader = imageio.get_reader(video)
                writer = imageio.get_writer(dest)
                for frame in reader:
                    writer.append_data(frame[:, :, :])
                writer.close()

    def process_videos(self):
        """
        Does all video processing:
        Converts to mp4, rotates to appropriate angle, splits video into n versions for each subject, saves in /out
        """
        # Makes sure no files are in /out or /processing to prevent clogging
        self.clear_files()
        # (Attempts to) Converts any rogue video types to .mp4
        self.convert_video()
        codec = 'm', 'p', '4', 'v'
        fourcc = cv2.VideoWriter_fourcc(*codec)
        # Iterates through all mp4 files in /in
        for video in glob.glob('{}//**//*.mp4'.format(self.path), recursive=True):
            # Iterator for indexing
            count = 0
            name = os.path.basename(video)
            # Removes file type from file name
            name = name.split('.', 1)[0]
            # Gives the folder of the file, if one exists
            folder_name = os.path.basename(os.path.dirname(video))
            if folder_name == 'in':
                folder_name = ''
            capture = cv2.VideoCapture(video)
            if not capture.isOpened():
                print('Cannot open video')
                sys.exit()
            ok, frame = capture.read()
            if not ok:
                print('Cannot read video')
                sys.exit()
            # Gets the frame where the time trial starts
            start_frame = self.select_start(video)
            # Sets the start of the video to that frame - 1
            capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame - 1)
            # Re-initializes ok and frame to new start frame
            ok, frame = capture.read()
            # Finds the angle of rotation to correct the video skew and rotates the first frame for bbox selection
            angle = self.get_angle(frame)
            rotated = self.rotate_image(frame, angle)
            # Select bounding boxes, where the video will be cropped and tracking will watch
            bbox = cv2.selectROIs("Select", rotated)
            # Closes pop-ups as it iterates to prevent clutter
            cv2.destroyAllWindows()
            for index in bbox:
                # Appends name, position from selected bounding boxes, and file location to a df
                concat_df = pd.DataFrame({'name': [('{}{}&{}'.format(folder_name, name, count + 1))],
                                          'startFrame': start_frame, '0': bbox[count][0], '1': bbox[count][1],
                                          '2': bbox[count][2], '3': bbox[count][3], 'angle': angle, 'file': video})

                self.df = pd.concat([self.df, concat_df], ignore_index=True)
            count += 1
        count = 0
        for i in range(len(self.df)):
            # Sets video from file location at index in df
            capture = cv2.VideoCapture(self.df.iloc[count, 7])
            # Sets frame to startFrame allow repeating the video for multiple bounding boxes
            capture.set(cv2.CAP_PROP_POS_FRAMES, self.df.iloc[count, 1])
            # Specifies output location, fourcc, fps, and frame size
            out = cv2.VideoWriter('videos\\out\\{}.mp4'.format(self.out_iter), fourcc, 30.0,
                                  (self.df.iloc[count, 4], self.df.iloc[count, 5]))
            ok, frame = capture.read()
            print('Cropping {}'.format(self.df.iloc[count, 0]))

            # Counts total frames in each sub-video
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            # Iterates while a new frame is found, ie for the duration of the video
            while ok:
                # Calculates current frame in video, breaks if it meets the final frame
                currFrame = int(capture.get(cv2.CAP_PROP_POS_FRAMES))
                if currFrame == frame_count:
                    break

                # Skips every x frames for each one recorded
                if currFrame % self.frame_modulo != 0:
                    ok, frame = capture.read()
                    continue
                # Rotates each frame to level it
                if self.df.iloc[count, 6] != 0:
                    frame = self.rotate_image(frame, self.df.iloc[count, 6])
                # Crops video into the determined bounding box and writes each box to a new file
                cropped_vid = frame[self.df.iloc[count, 3]: self.df.iloc[count, 3] + self.df.iloc[count, 5],
                              self.df.iloc[count, 2]: self.df.iloc[count, 2] + self.df.iloc[count, 4]]
                out.write(cropped_vid)
                ok, frame = capture.read()
            count += 1
            self.out_iter += 1

    def track_mice(self, video):
        """Tracking algorithm edited from tracktor, see tracktor.py and citation"""
        # colours is a vector of BGR values which are used to identify individuals in the video
        # since we only have one individual, the program will only use the first element from this array
        # i.e. (0,0,255) - red number of elements in colours should be greater than n_inds
        # (THIS IS NECESSARY FOR VISUALISATION ONLY)
        n_inds = 1
        colours = [(0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 255), (255, 255, 0), (255, 0, 0), (0, 255, 0),
                   (0, 0, 0)]

        # this is the block_size and offset used for adaptive thresholding (block_size should always be odd)
        # these values are critical for tracking performance
        block_size = 103
        offset = 40

        # the scaling parameter can be used to speed up tracking if video resolution is too high (use value 0-1)
        scaling = 0.75

        # minimum area and maximum area occupied by the animal in number of pixels, this parameter is used to get rid
        # of other objects in view that might be hard to threshold out but are differently sized
        min_area = 1000
        max_area = 3500

        # mot determines whether the tracker is being used in noisy conditions to track a single object or for
        # multi-object using this will enable k-means clustering to force n_inds number of animals
        mot = False

        # name of source video and paths
        video = os.path.basename(video).split('.', 1)[0]
        input_vidpath = 'videos\\out\\' + video + '.mp4'
        # outName = self.df.iloc[int(os.path.basename(video).split('.', 1)[0]), 0])
        output_filepath = 'processing\\' + self.df.iloc[int(os.path.basename(video).split('.', 1)[0]), 0] + '.csv'

        # Open video
        cap = cv2.VideoCapture(input_vidpath)
        if not cap.isOpened():
            sys.exit('Cannot read video')

        # Individual location(s) measured in the last and current step
        meas_last = list(np.zeros((n_inds, 2)))
        meas_now = list(np.zeros((n_inds, 2)))

        last = 0
        df = []
        pos_df = pd.DataFrame(columns=['maxx', 'maxy', 'minx', 'miny'])
        if self.df.iloc[int(os.path.basename(video).split('.', 1)[0]), 0]:
            print("Tracking {}".format(self.df.iloc[int(os.path.basename(video).split('.', 1)[0]), 0]))
        else:
            return

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            this = cap.get(1)
            if ret:
                frame = cv2.resize(frame, None, fx=scaling, fy=scaling, interpolation=cv2.INTER_LINEAR)
                thresh = tr.colour_to_thresh(frame, block_size, offset)
                final, contours, meas_last, meas_now = tr.detect_and_draw_contours(frame, thresh, meas_last, meas_now,
                                                                                   min_area, max_area)

                # Makes sure each measurement exists to prevent failure in hungarian algorithm
                if meas_now and meas_last:
                    new_contours = np.array(contours, dtype=object)
                    # Verifies that contours were created properly
                    if len(new_contours.shape) == 4:
                        try:
                            new_contours = np.reshape(new_contours, (new_contours.shape[1], new_contours.shape[3]))
                            loc_df = pd.DataFrame(new_contours, columns=['x', 'y'])
                            maxx = loc_df['x'].max()
                            maxy = loc_df['y'].max()
                            minx = loc_df['x'].min()
                            miny = loc_df['y'].min()
                            concat_df = pd.DataFrame({'maxx': maxx, 'maxy': maxy, 'minx': minx, 'miny': miny})
                            pos_df = pd.concat([pos_df, concat_df], ignore_index=True)
                        except ValueError:
                            print('Tracking error, skipped frame')
                    else:
                        continue

                    row_ind, col_ind = tr.hungarian_algorithm(meas_last, meas_now)
                    final, meas_now, df = tr.reorder_and_draw(final, colours, n_inds, col_ind, meas_now, df, mot,
                                                              this)

                    # Create output dataframe
                    for i in range(n_inds):
                        df.append([this, meas_now[i][0], meas_now[i][1]])

                    # Uncomment to display the video and tracking overlay
                    # cv2.imshow('frame', final)

                    if cv2.waitKey(1) == 27 or meas_now[0][0] < 20 or meas_now[0][0] > cap.get(3) - 20 or \
                            meas_now[0][1] < 20 or \
                            meas_now[0][1] > cap.get(4) - 20:
                        break

            if last >= this:
                break

            last = this

        # Write positions to file
        df = pd.DataFrame(np.matrix(df), columns=['frame', 'pos_x', 'pos_y'])
        df = df.join(pos_df)
        df.to_csv(output_filepath, sep=',')

        # When everything done, release the capture
        cap.release()
        # out.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    def detect_behavior(self):
        """Uses the positional data from the video to detect behaviors"""
        results = pd.DataFrame(columns=['video', 'rears', 'stretches'])
        for file in glob.glob('processing\\*.csv'):
            # Sets dataframe the the pos data from tracking function
            count_df = pd.read_csv(file, index_col=0)

            # Calculates the 'rectangularity' of the mouse
            count_df['xdiff'] = (count_df['maxy'] - count_df['miny']) / (count_df['maxx'] - count_df['minx'])

            # Modifiers to determine counting threshold, determined by comparing euklidean distance and cosine
            # similarity over their full range
            REAR_MOD = .94
            STRETCH_MOD = 1.94

            # Squares and divides by average all values in df to increase distinction
            count_df['miny'] = np.square(count_df['miny']) / (count_df['miny'].mean() -
                                                              (count_df['miny'].mean() * REAR_MOD))
            count_df['xdiff'] = np.square(count_df['xdiff']) / (count_df['xdiff'].mean() +
                                                                (count_df['xdiff'].mean() * STRETCH_MOD))

            # Finds the average value of the position data and determines a threshold for spikes
            pos_avg_y = count_df['miny'].mean()
            pos_avg_x = count_df['xdiff'].mean()
            pos_avg_y -= pos_avg_y * REAR_MOD
            pos_avg_x += pos_avg_x * STRETCH_MOD

            # Sets the time around each spike so as to only count one instance as one rear, 30 frames is 1 second
            frame_freeze = 360
            # Converts the delay threshold to be relative to the counting threshold, scales fps to whatever it is now
            frame_freeze = int(frame_freeze / self.frame_modulo)
            # Creates an array of values from pos y, makes them negative since our spikes are actually dips
            arr_y = count_df['miny'].values * -1
            arr_x = count_df['xdiff'].values
            # Finds peaks using scipy's find_peaks function
            peaks_y, _ = find_peaks(arr_y, height=-pos_avg_y, distance=frame_freeze)
            peaks_x, _ = find_peaks(arr_x, height=pos_avg_x, distance=frame_freeze)

            # Finds the video name from the file index
            vid_name = os.path.basename(file).split('.', 1)[0]

            # Prints the number of peaks, ie the number of rears detected
            rears = len(count_df['miny'][peaks_y])
            print("Rears detected in {}: {}".format(vid_name, rears))
            stretches = len(count_df['xdiff'][peaks_x])
            print("Stretches detected in {}: {}".format(vid_name, stretches))

            # Produces a chart, you can roughly follow it in the video if desired
            plt.plot(arr_y)
            plt.plot(peaks_y, arr_y[peaks_y], "x")
            plt.axhline(y=-pos_avg_y, color='red')
            plt.savefig('results\\{} rear plot.png'.format(vid_name))
            # Clears each plot and resets axes
            plt.clf()

            # Repeats the above for stretches
            plt.plot(arr_x)
            plt.plot(peaks_x, arr_x[peaks_x], 'x')
            plt.axhline(y=pos_avg_x, color='red')
            plt.savefig('results\\{} stretch plot.png'.format(vid_name))
            plt.clf()

            # Writes results to a dataframe
            concat_df = pd.DataFrame({'video': vid_name, 'rears': rears, 'stretches': stretches})
            results = pd.concat([results, concat_df], ignore_index=True)

        # Outputs the results of each analysis into a csv
        results.to_csv('results\\results.csv', index=False)

        # Clears generated files are in //out or //processing
        self.clear_files()


start_time = time.time()
run = Automate()
run.process_videos()
for file in glob.glob('videos\\out\\*.mp4'):
    run.track_mice(file)
run.detect_behavior()

print("Processed in {} minutes".format(round((time.time() - start_time) / 60, 5)))
