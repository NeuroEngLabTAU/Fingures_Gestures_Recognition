from psychopy import visual, core, event, gui, data
from psychopy.hardware import keyboard
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED)
import os
from PIL import Image
import random
from pathlib import Path
import argparse
from threading import Thread
from multiprocessing import Process
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np

try:
    from Leap import LeapRecorder, LeapVisuzalizer
except:
    print("Leap Motion SDK not found. Leap Motion data will not be recorded.")

from streamer import Data, Viz, EmgVisualizer



class Experiment:
    def __init__(self, num_repetaions=5, gesture_duration=5, rest_duration=5, gesture_directory=None, record=False):

        self.color_palette = {
            'background': (0.9, 0.9, 0.9),  # Light gray for background
            'text': (-1, -1, -1),  # Black for text
            'pause_button': (0.4, 0.4, 0.8),  # Blue for pause button
            'stop_button': (0.8, 0.4, 0.4),  # Red for stop button
        }
        
        self.num_repetaions = num_repetaions
        self.gesture_duration = gesture_duration
        self.rest_duration = rest_duration
        self.current_gesture_index = 0
        self.gesture_directory = gesture_directory
        self.record = record
        self.exp_info = {}
        self.exp_num = 0
        self.quit_key = 'q'



        self.data_dir = Path(__file__).parent.parent / 'dataset'

        # makedir if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # recording objects
        self.emg_data = None
        self.leap_data = None

    def _init_window(self):

        # Setup window
        try:
        # Setup window
            self.window = visual.Window(
                                size=(1000, 800), 
                                fullscr=False,
                                screen=0,
                                allowGUI=True,
                                allowStencil=False,
                                monitor='testMonitor',
                                colorSpace='rgb',
                                color=self.color_palette['background'],
                                blendMode='avg',
                                # useFBO=True, 
                                units='height')
            
                # ... (rest of your initialization code)
            self.exp_info['frameRate'] = self.window.getActualFrameRate()
            self.clock = core.Clock()
            welcome_text = 'A series of images will be shown on screen.\n\n\n' \
                    'Perform the gesture only when\n"Perform gesture"\nis written above the image.\n\n\n' \
                    'Relax your arm between gestures.\n\n\n' \
                    '(Press space when ready.)'
            # Window components
            self.instructions_text = visual.TextStim(self.window, text=welcome_text, color=self.color_palette['text'], height=0.05)
            self.countdown_text = visual.TextStim(self.window, text='', pos=(0, 0), color=self.color_palette['text'])
            self.exp_end_text = visual.TextStim(self.window, text='Experiment Complete!', color=self.color_palette['text'])
            self.running = False
        except Exception as e:
            print(f"Error during window initialization: {e}")

        # Experiment setup
        self.gesture_images, self.gesture_names = self.load_gesture_images(self.gesture_directory)
        self.num_completed = [0 for _ in self.gesture_images]

    def collect_participant_info(self):
        info_dialog = gui.Dlg(title='Participant Information')
        info_dialog.addField('Participant ID:')
        info_dialog.addField('Age:')
        info_dialog.addField('Gender:', choices=['Male', 'Female'])
        info_dialog.addField('Session:', choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        info_dialog.addField('Position:', choices=['1', '2', '3', '4', '5'])
        info_dialog.show()
        if info_dialog.OK:
            return {
                'Participant': info_dialog.data[0],
                'Age': info_dialog.data[1],
                'Gender': info_dialog.data[2],
                'session': info_dialog.data[3],
                'position': info_dialog.data[4]
            }
        else:
            core.quit()
    

    def resize_and_crop(self, pil_image):
        screen_width, screen_height = 800, 600
        print(screen_width, screen_height)
        image_width, image_height = pil_image.size
        image_aspect = image_width / image_height
        screen_aspect = screen_width / screen_height
        

        if image_aspect > screen_aspect:
            new_width = int(image_aspect * screen_height)
            pil_image = pil_image.resize((new_width, screen_height))
        else:
            new_height = int(screen_width / image_aspect)
            pil_image = pil_image.resize((screen_width, new_height))

        crop_x = (pil_image.width - screen_width) / 2
        crop_y = (pil_image.height - screen_height) / 2
        cropped_image = pil_image.crop((crop_x, crop_y, crop_x + screen_width, crop_y + screen_height))
        return cropped_image

    def load_gesture_images(self, gesture_directory):
        gesture_images = []
        image_names = []
        gesture_files = os.listdir(gesture_directory)
        for file_name in gesture_files:
            file_name = file_name.lower()
            if file_name.endswith('.png') or file_name.endswith('.jpg'):
                image_path = os.path.join(gesture_directory, file_name)
                pil_image = Image.open(image_path)
                pil_image = self.resize_and_crop(pil_image)
                image = visual.ImageStim(self.window, image=pil_image)
                gesture_images.append(image)
                image_names.append(file_name.split('.')[0])
        
        return gesture_images, image_names

    def check_quit_key(self):
        if event.getKeys(keyList=[self.quit_key]):
            core.quit()
    
    
    def pause_experiment(self):
        self.running = False
        while True:
            self.instructions_text.text = 'Experiment Paused. Press space to resume or q to quit.'
            self.instructions_text.draw()
            self.window.flip()
            keys = event.waitKeys(keyList=['space', 'q'])
            if 'space' in keys:
                self.running = True
                return
            elif 'q' in keys:
                core.quit()
    
    def stop_experiment(self):
        self.running = False

    def show_countdown(self, duration):
        for i in range(duration, 0, -1):
            self.countdown_text.text = f"Next gesture in {i} seconds"
            self.countdown_text.draw()
            self.window.flip()
            core.wait(1)

    def show_gesture(self):
        gesture_image = self.gesture_images[self.current_gesture_index]
        gesture_image.draw()
        self.window.flip()
        self.trigger(f'start_{self.gesture_names[self.current_gesture_index]}')
        core.wait(5)  # Display the gesture for 5 seconds
    
    def update_gesture(self):

        # Choose a random gesture that has not been completed enough times
        self.current_gesture_index = random.randint(0, len(self.gesture_images)-1)
        self.num_completed[self.current_gesture_index] += 1

        # Remove the gesture if it has been completed enough times
        if self.num_completed[self.current_gesture_index] == self.num_repetaions:
            self.gesture_images.pop(self.current_gesture_index)

        # return fasle if there are no more gestures to display
        if len(self.gesture_images) == 0:
            return False
        else:
            return True
        
    def trigger(self, msg, verbose=True):
        
        if self.emg_data is not None:
            self.emg_data.add_annotation(msg)
            if verbose:
                print(f'TRIGGER: {self.emg_data.annotations[-1]}')
        elif verbose:
            print(f'TRIGGER: {msg}')


    def do_experiment(self):

        self._init_window()

        print(f"running experiment with {len(self.gesture_images)} gestures")

        # show instructions
        self.instructions_text.draw()

        self.window.flip()
        event.waitKeys(keyList=['space'])

        self.show_countdown(self.rest_duration)  # Display countdown for 5 seconds

        self.running = True
        while self.running:
            keys = event.getKeys()
            if self.quit_key in keys:
                self.stop_experiment()
                break
            elif 'space' in keys:
                self.pause_experiment()
                continue
            
            self.show_gesture()
            if self.record:
                self.trigger(f'end_{self.gesture_names[self.current_gesture_index]}')   
            self.show_countdown(self.rest_duration)  
            # self.do_transition()  
            if not self.update_gesture():
                break
        
        if self.record:
            self.trigger('end_experiment')
            self.emg_data.stop()
            self.leap_data.stop()

            self.emg_data.join()
            self.leap_data.join()
        

        self.exp_end_text.draw()
        self.window.flip()
        core.wait(3)

        self.window.close()
    
    def do_visualise(self):

         # Visualize data stream in main thread:
        secs = 10             # Time window of plots (in seconds)
        ylim = (-1000, 1000)  # y-limits of plots
        ica = False           # Perform and visualize ICA alongside raw data
        update_interval = 10  # Update plots every X ms
        max_points = 250      # Maximum number of data points to visualize per channel (render speed vs. resolution)

        
        if self.record:
            emg_viz = Viz(self.emg_data, window_secs=secs, plot_exg=True, plot_imu=False, plot_ica=ica,
                    update_interval_ms=update_interval, ylim_exg=ylim, max_points=250)

            emg_viz.start()
        else:
            # sample animation using matplotlib.animation
            

            fig, ax = plt.subplots()
            ax.set_xlim(0, 2*np.pi)
            ax.set_ylim(-1, 1)
            line, = ax.plot([], [])

            anim = FuncAnimation(fig, self.update, frames=np.arange(0, 2*np.pi, 0.1), fargs=(line,), interval=10)
            plt.show()
            

    @staticmethod
    def update(i, line):
        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x + i)
        line.set_data(x, y)

    def pre_exp(self, emg_data):
        '''
        Pre experiment setup
        '''
        # self.exp_info = self.collect_participant_info()
        # self._init_window()
        # print(f"running experiment with {len(self.gesture_images)} gestures")
        # self.instructions_text.draw()
        # self.window.flip()
        # event.waitKeys(keyList=['space'])
        # self.show_countdown(self.rest_duration)

        # Visualize data stream in main thread:
        secs = 10             # Time window of plots (in seconds)
        ylim = (-1000, 1000)  # y-limits of plots
        ica = False           # Perform and visualize ICA alongside raw data
        update_interval = 10  # Update plots every X ms
        max_points = 250      # Maximum number of data points to visualize per channel (render speed vs. resolution)

        # emg_data.start()

        # plot leap data
        leap_viz = LeapVisuzalizer()
        leap_viz.start()

        # plot emg data
        
        emg_data.start()
        emg_viz = Viz(emg_data, window_secs=secs, plot_exg=True, plot_imu=False, plot_ica=ica,
                update_interval_ms=update_interval, ylim_exg=ylim, max_points=250)

        emg_viz.start()
        print("terminated")
        leap_viz.stop()
        leap_viz.join()


    def run(self,emg_Data, leap_data):

        '''
        Main function to run the experiment
        '''
        # setup window
        self._init_window()

        # collect participant info
        self.exp_info = self.collect_participant_info()
        self.emg_data = emg_Data
        self.leap_data = leap_data

        # thread = Thread(target=self.do_experiment)
        # thread.start()
        print(f"running experiment with {len(self.gesture_images)} gestures")

        # show instructions
        self.instructions_text.draw()

        self.window.flip()
        event.waitKeys(keyList=['space'])

        self.show_countdown(self.rest_duration)  # Display countdown for 5 seconds

        self.running = True
        if (self.record):
            self.exp_info['date'] = data.getDateStr()  # add a simple timestamp
            self.exp_info['expName'] = 'fpe - real time'
            self.exp_info['psychopyVersion'] = '2023.2.3'

            self.data_dir = Path(self.data_dir, self.exp_info['Participant'].rjust(3, '0'), f"S{self.exp_info['session']}")
            self.data_dir.mkdir(parents=True, exist_ok=True)

            with open(Path(self.data_dir, "log.txt"), 'w') as f:
                f.write(f"{self.exp_info}\n")
            # start recording
            self.emg_data.save_as = str(Path(self.data_dir, f"fpe_pos{self.exp_info['position']}_{self.exp_info['Participant'].rjust(3, '0')}_S{self.exp_info['session']}_rep{self.exp_num}_BT.edf"))
            self.leap_data.save_as = str(Path(self.data_dir, f"fpe_pos{self.exp_info['position']}_{self.exp_info['Participant'].rjust(3, '0')}_S{self.exp_info['session']}_rep{self.exp_num}_BT.csv"))
            print(f"Saving data to: {self.emg_data.save_as}")
            
            self.emg_data.start()
            self.leap_data.start()

        while self.running:
            keys = event.getKeys()
            if self.quit_key in keys:
                self.stop_experiment()
                break
            elif 'space' in keys:
                self.pause_experiment()
                continue
            
            self.show_gesture()
            if self.record:
                self.trigger(f'end_{self.gesture_names[self.current_gesture_index]}')   
            self.show_countdown(self.rest_duration)  
            # self.do_transition()  
            if not self.update_gesture():
                break
        
        self.exp_end_text.draw()
        self.window.flip()
        core.wait(3)

        self.window.close()

        
        
        print("terminated")
        
    def start_processes(self, emg_data, leap_data):

        self.emg_data = emg_data
        self.leap_data = leap_data

        if (self.record):
            self.exp_info['date'] = data.getDateStr()  # add a simple timestamp
            self.exp_info['expName'] = 'fpe - real time'
            self.exp_info['psychopyVersion'] = '2023.2.3'

            self.data_dir = Path(self.data_dir, self.exp_info['Participant'].rjust(3, '0'), f"S{self.exp_info['session']}")
            self.data_dir.mkdir(parents=True, exist_ok=True)

            with open(Path(self.data_dir, "log.txt"), 'w') as f:
                f.write(f"{self.exp_info}\n")
            # start recording
            self.emg_data.save_as = str(Path(self.data_dir, f"fpe_pos{self.exp_info['position']}_{self.exp_info['Participant'].rjust(3, '0')}_S{self.exp_info['session']}_rep{self.exp_num}_BT.edf"))
            self.leap_data.save_as = str(Path(self.data_dir, f"fpe_pos{self.exp_info['position']}_{self.exp_info['Participant'].rjust(3, '0')}_S{self.exp_info['session']}_rep{self.exp_num}_BT.csv"))
            print(f"Saving data to: {self.emg_data.save_as}")
            
            self.emg_data.start()
            self.leap_data.start()
        else:
            self.emg_data = testClass()
            self.leap_data = testClass()
            self.emg_data.start()
            self.leap_data.start()
        
        exp_process = Thread(target=self.do_experiment)
        exp_process.start()

        # vis_process = Process(target=self.do_visualise)
        self.do_visualise()
        # vis_process.start()

        


        exp_process.join()
        # vis_process.join()

        if self.record:
            self.trigger('end_experiment')
            self.emg_data.stop()
            self.leap_data.stop()

            self.emg_data.join()
            self.leap_data.join()




def main(args):
    gesture_dir = './images'
    save_dir = './data'


    # experiment setup
    num_repetaions = 5
    gesture_duration = 5
    rest_duration = 5
    record = False
    
    host = '127.0.0.1'
    port = 20001
    timeout = 20
    verbose = False

    if record:
        emg_data = Data(host_name=host, port=port, timeout_secs=timeout, verbose=verbose, save_as="test.edf")
        leap_data = LeapRecorder(save_dir)
    else:
        emg_data = None
        leap_data = None


    experiment = Experiment(num_repetaions, gesture_duration, rest_duration, gesture_directory=gesture_dir, record=record)
    
    if args.vis:
        experiment.pre_exp(emg_data=emg_data)
    else:
        experiment.start_processes(emg_data=emg_data, leap_data=leap_data)


class testClass(Thread):
    def __init__(self):
        super().__init__()
        self.is_runnig = False
    
    def run(self):
        print("test")
        self.is_runnig = True
        while self.is_runnig:
            core.wait(1)
            print("test2")
    
    def stop(self):
        print("stop")
        self.is_runnig = False
        self.join()
        print("stopped")

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--vis', action='store_true', help='Visualize data stream')

    args = argparser.parse_args()
    main(args)
    

