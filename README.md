# ISOForge Bootloader

- A simple multiboot USB maker CLI tool built with Python.

## Project Folder Structure:

```bash
ISOForge Bootloader/
  ├── main.py
  ├── dd.exe
  ├── EFI/
  │    └── BOOT/
  │         └── bootx64.efi
  └── boot/
       └── grub/
            ├── grub.cfg
            ├── themes/
            │    └── isoforge/
            │         ├── theme.txt
            │         └── background.png
            ├── i386-pc/
            └── x86_64-efi/
```

## How Project Works:

1. Detects connected Drivers
2. User selects which USB driver to use
3. Partitions USB into two partitions:
   - Partition 1: FAT32 (ISOFORGE) - bootloader files
   - Partition 2: NTFS (STORAGE) - ISO files, and user personal files
4. Copies boot/ and EFI/ folder to Partition 1
5. Writes boot.img to USB MBR
6. Writes core.img after MBR
7. USB is ready - User create "ISOs/" folder and copies ISO files to Partition 2

## USB Structure After Set-up:

```bash
USB Partition 1 (FAT32 - ISOFORGE)/
  ├── EFI/BOOT/bootx64.efi
  └── boot/grub/
       ├── grub.cfg
       ├── i386-pc/
       └── x86_64-efi/

USB Partition 2 (NTFS - STORAGE)/
  └── ISOs/
       └── (user puts ISO files here)
```

## Python Libraries:

1. Psutil - https://psutil.readthedocs.io/stable/ - USB drive detection
2. Subprocess - https://docs.python.org/3/library/subprocess.html - Run system commands
3. Shutil - https://docs.python.org/3/library/shutil.html - Copy files and folders
4. Pathlib - https://docs.python.org/3/library/pathlib.html - File path handling
5. OS - https://docs.python.org/3/library/os.html - System operations
6. Ctypes - https://docs.python.org/3/library/ctypes.html - Windows API command

## External Tools:

1. Diskpart - https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/diskpart

## GRUB Documentation

1. Official Manual - https://www.gnu.org/software/grub/manual/grub/grub.html
2. Arch Wiki Grub: https://wiki.archlinux.org/title/GRUB
3. File Download - https://ftp.gnu.org/gnu/grub/ - This project uses grub-2.14-for-windows.zip

## WSL Setup (one time only):

### Requirements

```bash
sudo apt install grub-pc-bin grub-efi-amd64-bin xorriso mtools qemu-system-x86 -y
```

## Generating core.img (WSL):

### Step 1 — Create grub_early.cfg

- This file is embedded into both core.img and bootx64.efi so GRUB automatically finds the USB on any computer.

```bash
cat > ~/grub_early.cfg << 'EOF'
search --no-floppy --label --set=root ISOFORGE
set prefix=($root)/boot/grub
configfile ($root)/boot/grub/grub.cfg
EOF
```

### Step 2 — Generate core.img

```bash
grub-mkimage -o ~/core.img -O i386-pc -p "/boot/grub" -c ~/grub_early.cfg biosdisk part_msdos part_gpt fat ext2 ntfs iso9660 search search_fs_file search_fs_uuid search_label configfile normal linux linux16 loopback echo ls reboot halt sleep test regexp all_video gfxterm gfxmenu gfxterm_background video video_fb png jpeg

### Copy and move core.img to i386-pc
cp ~/core.img /mnt/c/Projects/Python/ISOForge\ Bootloader/boot/grub/i386-pc/
```

## Generating bootx64.efi for UEFI

```bash
#### Create another grub_early.cfg

grub-mkimage -o ~/bootx64.efi -O x86_64-efi -p "/boot/grub" -c ~/grub_early.cfg part_msdos part_gpt fat ext2 ntfs iso9660 search search_fs_file search_fs_uuid search_label configfile normal linux linux16 loopback echo ls reboot halt sleep test regexp all_video gfxterm gfxmenu gfxterm_background video video_fb png jpeg

### Copy and move bootx64 to EFI/boot/
cp ~/bootx64.efi /mnt/c/Projects/Python/ISOForge\ Bootloader/EFI/boot/
```

## Testing GRUB with QEMU (WSL):

### Copy boot folder to WSL home

```bash
cp -r /mnt/c/Projects/Python/ISOForge\ Bootloader/boot ~/isoforge/
```

### Generate ISO

```bash
sudo grub-mkrescue -o ~/isoforge.iso ~/isoforge/
```

### Copy ISO back to Windows

```bash
cp ~/isoforge.iso /mnt/c/Projects/Python/ISOForge\ Bootloader/
```

### Test with QEMU

```bash
qemu-system-x86_64 -cdrom /mnt/c/Projects/Python/ISOForge\ Bootloader/isoforge.iso -boot d -m 512
```

## Convert main.py to executable file .exe

### Step 1 - Install pyinstaller library

```bash
py -m pip install pyinstaller
```

### Step 2 - Conver .py to .exe

```bash
py -m PyInstaller --onedir --add-data "boot;boot" --add-data "EFI;EFI" --name "ISOForge" main.py

### The .exe file will on dist/ISOForge/ folder
### Manually copy&paste boot/,EFI, and other files to dist/ISOForge/ folder
```

### AI Assisted sections:

1. Diskpart output parsing - extracting disk numbers from list disk output
2. write_boot_img() - Writing boot.img to USB MBR using Windows API (ctypes)
3. write_core_img() - Writing core.img after MBR using Windows API (ctypes)
