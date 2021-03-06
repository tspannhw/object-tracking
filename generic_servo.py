import logging
import time
from threading import Event
from threading import Thread

logger = logging.getLogger(__name__)

class Servo(object):
    def __init__(self, name, alternate=False, secs_per_180=0.50, pix_per_degree=6.5):
        self.__alternate = alternate
        self.__secs_per_180 = secs_per_180
        self.__ppd = pix_per_degree
        self.ready_event = Event()
        self.__thread = None
        self.__stopped = False
        logger.info("Created servo: {0} alternate={1} secs_per_180={2} pix_per_degree={3}"
                    .format(self.name, self.__alternate, self.__secs_per_180, self.__ppd))
        self.name = name

    def get_currpos(self):
        return -1

    def set_angle(self, val, pause=None):
        pass

    def run_servo(self, forward, loc_source, other_ready_event):
        logger.info("Started servo: {0}".format(self.name))
        while not self.__stopped:
            try:
                if self.__alternate:
                    self.ready_event.wait()
                    self.ready_event.clear()

                # Get latest location
                img_pos, img_total, middle_inc, id_val = loc_source()

                # Skip if object is not seen
                if img_pos == -1 or img_total == -1:
                    logger.info("No target seen: {0}".format(self.name))
                    continue

                midpoint = img_total / 2

                curr_pos = self.get_currpos()

                if img_pos < midpoint - middle_inc:
                    err = abs(midpoint - img_pos)
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos + adj if forward else curr_pos - adj
                    # print("{0} off by {1} pixels going from {2} to {3} adj {4}"
                    #      .format(self.__name, err, curr_pos, new_pos, adj))
                elif img_pos > midpoint + middle_inc:
                    err = img_pos - midpoint
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos - adj if forward else curr_pos + adj
                    # print("{0} off by {1} pixels going from {2} to {3} adj {4}"
                    #      .format(self.__name, err, curr_pos, new_pos, adj))
                else:
                    continue

                delta = abs(new_pos - curr_pos)

                # If you do not pause long enough, the servo will go bonkers
                # Pause for a time relative to distance servo has to travel
                wait_time = (self.__secs_per_180 / 180) * delta

                # Write servo value
                self.set_angle(new_pos, pause=wait_time)

            finally:
                if self.__alternate and other_ready_event is not None:
                    other_ready_event.set()

            time.sleep(.10)

    def start(self, forward, loc_source, other_ready_event):
        self.__thread = Thread(target=self.run_servo, args=(forward, loc_source, other_ready_event))
        self.__thread.start()

    def join(self):
        self.__thread.join()

    def stop(self):
        logger.info("Stopping servo {0}".format(self.name))
        self.__stopped = True
