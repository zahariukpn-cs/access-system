import json
import sys
import time
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Встановіть бібліотеку pyserial: pip install pyserial")
    sys.exit(1)


def find_esp_port(preferred_port=None):
    ports = list(serial.tools.list_ports.comports())
    available = {p.device.upper(): p.device for p in ports}

    if preferred_port:
        if preferred_port.upper() in available:
            return available[preferred_port.upper()]
        print(f"Помилка: порт {preferred_port} не знайдено. Доступні: {', '.join(available.values()) or 'немає'}")
        sys.exit(1)

    if "COM8" in available:
        return available["COM8"]

    if not ports:
        print("Помилка: жодного COM-порту не знайдено. Перевірте USB-кабель ESP32.")
        sys.exit(1)

    for p in ports:
        desc = (p.description or "").lower()
        if any(k in desc for k in ("cp210", "ch340", "usb", "uart", "serial")):
            return p.device
    return ports[0].device


def read_response(ser, initial_wait=2.5):
    ser.timeout = initial_wait
    lines = []
    while True:
        raw = ser.readline()
        if not raw:
            break
        line = raw.decode("utf-8", errors="replace").rstrip()
        if line:
            lines.append(line)
        ser.timeout = 0.3
    return lines


def main():
    snapshot_path = Path("snapshot.json")
    read_logs_mode = "--logs" in sys.argv
    show_db_mode = "--db" in sys.argv
    port_arg = next((a for a in sys.argv[1:] if a.upper().startswith("COM")), None)

    port = find_esp_port(port_arg)
    print(f"Підключення до ESP32 на {port}...")

    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.dtr = False
    ser.rts = False
    ser.open()

    try:
        ser.dtr = False
        ser.rts = False
        time.sleep(2.0)
        ser.reset_input_buffer()

        if read_logs_mode:
            ser.write(b"SHOW_LOGS\n")
        elif show_db_mode:
            ser.write(b"SHOW_DB\n")
        else:
            if not snapshot_path.exists():
                print("Помилка: файл snapshot.json не знайдено у поточній папці.")
                sys.exit(1)
            data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            compact_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            print(f"Відправка snapshot.json ({len(compact_json)} байт)...")
            payload = f"UPDATE_DB:{compact_json}\n".encode("utf-8")
            ser.write(payload)

        ser.flush()
        lines = read_response(ser)
        if lines:
            for line in lines:
                print(line)
        else:
            print("ESP32 не відповіла. Натисніть кнопку EN (Reset) на платі й спробуйте ще раз.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
