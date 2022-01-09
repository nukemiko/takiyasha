import argparse
import os
from typing import IO, Optional

from takiyasha.decryptions.algorithms.qmc import QMCDecrypter
from takiyasha.exceptions import DecryptFailed, DecryptionError


def print_progress(a: int, b: int):
    ratio = a / b * 100
    print('{:2f} ({}/{})'.format(ratio, a, b), end='\r')


ap = argparse.ArgumentParser()
ap.add_argument('file', type=argparse.FileType(mode='rb'))
ap.add_argument('-o', '--save', type=argparse.FileType(mode='wb'))
ap.add_argument('-s', '--noconfirm', action='store_true')
args = ap.parse_args()

file: IO[bytes] = args.file
save_file: Optional[IO[bytes]] = args.save
skip_confirm: bool = args.noconfirm

try:
    decrypter = QMCDecrypter.generate(file)
except DecryptionError:
    print("This file is decrypted by RC4-based QMCv2 algorithm, it's not support yet.")
    exit(1)
    raise SystemExit

try:
    audiofmt = decrypter.validate()
except DecryptFailed as exc:
    print('Decrypt failed: failed to recongize decrypted audio format.')
    exit(1)
    raise SystemExit

audiolen = decrypter.audio_length

if not save_file:
    save_filename = os.path.join(os.getcwd(), os.path.splitext(os.path.basename(file.name))[0] + f'.{audiofmt}')
else:
    save_filename = save_file.name

print(f'File name: {file.name}')
print(f'File size: {os.path.getsize(file.name)}')
print(f'Cipher: {type(decrypter.cipher).__name__}')
print(f'Decrypted file size: {audiolen}')
print(f'Decrypted file format: {audiofmt}')
if decrypter.raw_metadata_extra:
    print(f'raw_metadata_extra: {decrypter.raw_metadata_extra}')
print(f'Save to: {save_filename}')
print()
if not skip_confirm:
    try:
        input('Press Enter to continue, or press Ctrl-C to exit.')
        print()
    except KeyboardInterrupt:
        print('Decrypt cancelled.')
        exit(130)
        raise SystemExit

if not save_file:
    save_file = open(save_filename, 'wb')

for idx, byte in enumerate(decrypter.iter_decrypt(), start=1):
    byte_container = bytearray(1)
    byte_container[0] = byte
    save_file.write(byte_container)
else:
    print('Done.')
