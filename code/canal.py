import random, time, threading
from queue import Queue, Empty

# Cette classe simule un canal de communication avec des erreurs et des pertes de trames


class Channel:
    def __init__(self, probErreur, probPerte, delaiMax=0):
        self.probErreur = probErreur
        self.probPerte = probPerte
        self.delaiMax = delaiMax
        # Queue pour gérer les trames à envoyer
        self.queue = Queue()
        self._stop = threading.Event()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    # Méthode pour envoyer une trame à travers le canal
    def send(self, frame, deliver_callback):
        self.queue.put((frame, deliver_callback))

    # Méthode interne pour gérer l'envoi des trames avec délai, perte et corruption
    def _run(self):
        while not self._stop.is_set():
            try:
                frame, callback = self.queue.get(timeout=0.1)
            except Empty:
                continue
            if random.random() < self.probPerte:
                continue

            delay = random.uniform(0, self.delaiMax) / 1000.0
            time.sleep(delay)

            frame = self._maybe_corrupt(frame)
            try:
                callback(frame)
            except Exception as e:
                print("Channel callback error:", e)

    # Méthode interne pour éventuellement corrompre une trame
    def _maybe_corrupt(self, frame):
        if random.random() > self.probErreur:
            return frame
        if isinstance(frame, str):
            frame = frame.encode()
        data = bytearray(frame)
        if not data:
            return bytes(data)
        byte_i = random.randrange(len(data))
        bit_i = 1 << random.randrange(8)
        data[byte_i] ^= bit_i
        return bytes(data)

    # Méthode pour arrêter le canal proprement
    def stop(self):
        self._stop.set()
        self.worker.join()
