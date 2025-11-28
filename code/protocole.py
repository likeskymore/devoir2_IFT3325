import time
import threading
from datetime import datetime

from stuffing import FLAG, bit_stuff, bit_destuff
from canal import Channel


# Fonction utilitaire pour le logging avec timestamp
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}")


# Fonction permettant de convertir une chaîne de bits en bytes
def bits_to_bytes(bitstring: str) -> bytes:
    pad = (8 - len(bitstring) % 8) % 8
    bitstring += "0" * pad
    return int(bitstring, 2).to_bytes(len(bitstring) // 8, "big")


# Fonction permettant de convertir des bytes en une chaîne de bits
def bytes_to_bits(b: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in b)


# Fonction de calcul du CRC-16
def crc16(bits: str) -> str:
    poly = 0x1021
    crc = 0x0000

    for bit in bits:
        crc <<= 1
        if int(bit) ^ ((crc >> 16) & 1):
            crc ^= poly
        crc &= 0xFFFF

    return f"{crc:016b}"


# Fonction pour construire une trame avec en-tête, données, CRC et bit-stuffing
def build_frame(header_bits: str, data_bits: str) -> bytes:
    payload = header_bits + data_bits
    crc = crc16(payload)
    stuffed = bit_stuff(payload + crc)
    return bits_to_bytes(FLAG + stuffed + FLAG)


# Fonction pour analyser une trame reçue, vérifier le CRC et extraire les données
def parse_frame(frame_bytes: bytes):
    bits = bytes_to_bits(frame_bytes)
    start = bits.find(FLAG)
    end = bits.rfind(FLAG)
    # Vérification de la présence des flags
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Missing flags")
    inner = bits[start + len(FLAG) : end]
    destuffed = bit_destuff(inner)
    # Destuffing et vérification CRC
    payload = destuffed[:-16]
    recv_crc = destuffed[-16:]
    calc_crc = crc16(payload)
    header = payload[:8]
    data = payload[8:]
    if recv_crc != calc_crc:
        raise ValueError(f"CRC error detected for frame {int(header,2)}")
    return int(header, 2), data


# Implémentation du protocole Go-Back-N
def run_gbn(
    message: str, channel: Channel, timeout_ms=200, window_size=4, max_retries=10
):
    stats = {"sent": 0, "retransmitted": 0, "acks": 0, "received": 0}

    frames = []
    seq = 0
    # Diviser le message en trames de 100 octets chacune
    for i in range(0, len(message), 100):
        chunk = message[i : i + 100]
        data_bits = "".join(f"{ord(c):08b}" for c in chunk)
        header_bits = f"{seq % 256:08b}"
        frames.append(build_frame(header_bits, data_bits))
        seq += 1

    total_frames = len(frames)
    base = 0
    next_seq = 0
    # On met un lock pour éviter les conditions de course
    lock = threading.Lock()
    ack_event = threading.Event()
    last_ack_received = -1
    retry_counts = [0] * total_frames

    start_time = time.time()

    # Callback pour traiter les trames reçues (ACKs)
    def receiver_callback(frame_bytes):
        nonlocal last_ack_received, base

        stats["received"] += 1
        try:
            seqnum, _ = parse_frame(frame_bytes)
        except ValueError as e:
            log(e)
            return

        with lock:
            if seqnum > last_ack_received:
                last_ack_received = seqnum
                stats["acks"] += 1
                log(f"ACK received for {seqnum}")
                base = last_ack_received + 1
                ack_event.set()
            else:
                log(f"Ignored duplicate ACK for {seqnum}")

    # Boucle principale d'envoi des trames
    while base < total_frames:
        while next_seq < min(base + window_size, total_frames):
            log(f"Sending frame {next_seq}")
            stats["sent"] += 1
            channel.send(frames[next_seq], receiver_callback)
            next_seq += 1

        ack_event.clear()
        ok = ack_event.wait(timeout_ms / 1000)
        if ok:
            continue

        log(f"Timeout! Retransmitting window starting at {base}")
        for seqnum in range(base, next_seq):
            retry_counts[seqnum] += 1
            if retry_counts[seqnum] > max_retries:
                log(f"Max retries reached for frame {seqnum}, skipping it")
                base += 1  # Move the window forward
                continue
            log(f"Resending frame {seqnum} (retry {retry_counts[seqnum]})")
            stats["retransmitted"] += 1
            stats["sent"] += 1
            channel.send(frames[seqnum], receiver_callback)

    end_time = time.time()
    duration = end_time - start_time
    log("Transmission finished.")
    log(f"Frames sent: {stats['sent']}")
    log(f"Frames retransmitted: {stats['retransmitted']}")
    log(f"ACKs received: {stats['acks']}")
    log(f"Total time: {duration:.3f}s")


if __name__ == "__main__":
    with open("message.txt", "r", encoding="ascii") as f:
        msg = f.read()

    channel = Channel(probErreur=0.8, probPerte=0, delaiMax=0)

    run_gbn(msg, channel, timeout_ms=200, window_size=4)
    channel.stop()
