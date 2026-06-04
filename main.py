# Libraries/Modules
import os
import time
import psutil
import shutil
import ctypes
from pathlib import Path
import subprocess

# Tool Logo
def banner():
    banner = """
ISOForge Bootloader"""
    print(banner)

# Usb Detection
def devices_detected():
    usb_devices = []
    print("Devices Detected: ")
    partitions = psutil.disk_partitions()
    for p in partitions:
        if "removable" in p.opts:
            usb_devices.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype
            })
    
    for number, usb_detected in enumerate(usb_devices, start=1):
        print(f"{number}. Name: {usb_detected['device']}, Mountpoint: {usb_detected['mountpoint']}, Fstype: {usb_detected['fstype']}")

    return usb_devices

# Write boot.img to MBR while preserving partition table
def write_boot_img(disk_number, boot_img_path):
    drive = f"\\\\.\\PhysicalDrive{disk_number}"

    handle = ctypes.windll.kernel32.CreateFileW(
        drive,
        0x80000000 | 0x40000000,
        0x3,
        None,
        3,
        0,
        None
    )

    original_mbr = ctypes.create_string_buffer(512)
    bytes_read = ctypes.c_ulong(0)
    ctypes.windll.kernel32.SetFilePointer(handle, 0, None, 0)
    ctypes.windll.kernel32.ReadFile(handle, original_mbr, 512, ctypes.byref(bytes_read), None)

    with open(boot_img_path, "rb") as f:
        boot_data = f.read(512)

    merged = boot_data[:446] + original_mbr.raw[446:]

    ctypes.windll.kernel32.SetFilePointer(handle, 0, None, 0)
    written = ctypes.c_ulong(0)
    ctypes.windll.kernel32.WriteFile(handle, merged, 512, ctypes.byref(written), None)
    ctypes.windll.kernel32.CloseHandle(handle)

# Write core.img using Windows API
def write_core_img(disk_number, core_img_path):
    drive = f"\\\\.\\PhysicalDrive{disk_number}"
    
    with open(core_img_path, "rb") as f:
        core_data = f.read()
        padded = core_data + b'\x00' * (512 - len(core_data) % 512)

    handle = ctypes.windll.kernel32.CreateFileW(
        drive,
        0x40000000,
        0x3,
        None,
        3,
        0,
        None
    )

    ctypes.windll.kernel32.SetFilePointer(handle, 512, None, 0)
    written = ctypes.c_ulong(0)
    ctypes.windll.kernel32.WriteFile(handle, padded, len(padded), ctypes.byref(written), None)
    ctypes.windll.kernel32.CloseHandle(handle)

# Usb Bootloader Setup Process
def set_up():
    time.sleep(0.5)
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Disk Partations: ")
    result = subprocess.run(
        ["diskpart"],
        input="list disk\nexit\n",
        text=True,
        capture_output=True
    )
    lines = result.stdout.splitlines()

    disks = []
    for line in lines:
        if line.strip().startswith("Disk") and "GB" in line:
            print(line.strip())   
            parts = line.split()
            disks.append(parts[1])
    while True: 
        try:
            user_input = int(input("Enter Disk Number of the device: "))
            if str(user_input) in disks:
                print(f"Disk {user_input} selected")
                print("Warning: This will delete/erase all folders and files of the Device")
                confirm = input("Do you want to continue (Y/N): ")
                if confirm == "y" or confirm == "Y" or confirm == "Yes":
                    # Diskpart Process
                    time.sleep(0.5)
                    print("Processing please wait.....")
                    diskpart_command = f"""
select disk {user_input}
clean
create partition primary size=4096 offset=2048
format fs=fat32 quick label=ISOFORGE
active
assign

create partition primary
format fs=ntfs quick label=STORAGE
assign
exit
"""
                    diskpart_process = subprocess.run(
                        ["diskpart"],
                        input=diskpart_command,
                        text=True,
                        capture_output=True
                    )

                    print(diskpart_process.stdout)
                
                    # Moving boot/ folder to the 1st Partition of the USB
                    os.system('cls' if os.name == 'nt' else 'clear')
                    time.sleep(0.5)
                    print("Moving boot/ and EFI/ folder to the USB 1st Partition...")
                    time.sleep(0.5)
                    devices_detected()
                    folder_path1 = Path("boot")
                    folder_path2 = Path("EFI")
                    destination = Path(input("Partition 1 Assigned Letter (e.g. D:\\): "))
                    print("Processing please wait.....")
                    if folder_path1.exists() and folder_path2.exists():
                        target1 = destination / folder_path1.name
                        target2 = destination / folder_path2.name
                        shutil.copytree(folder_path1, target1, dirs_exist_ok=True)
                        shutil.copytree(folder_path2, target2, dirs_exist_ok=True)
                        print("boot/ and EFI/ transferred successfully")

                        # Installing bootloader
                        time.sleep(2)
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print("Processing please wait.....")
                        time.sleep(0.5)

                        # Write boot.img preserving partition table
                        write_boot_img(user_input, "boot/grub/i386-pc/boot.img")

                        # Rescan to unlock drive before writing core.img
                        subprocess.run(
                            ["diskpart"],
                            input=f"select disk {user_input}\noffline disk\nonline disk\nrescan\nexit\n",
                            text=True,
                            capture_output=True
                        )
                        time.sleep(3)

                        # Write core.img after MBR
                        write_core_img(user_input, "boot/grub/i386-pc/core.img")

                        # Force flush and release all handles
                        subprocess.run(
                            ["diskpart"],
                            input=f"select disk {user_input}\noffline disk\nonline disk\nexit\n",
                            text=True,
                            capture_output=True
                        )
                        time.sleep(2)

                        # Final rescan
                        subprocess.run(
                            ["diskpart"],
                            input=f"select disk {user_input}\nrescan\nexit\n",
                            text=True,
                            capture_output=True
                        )
                        os.system('cls' if os.name == 'nt' else 'clear')
                        time.sleep(3)
                        print("All process are done :)")
                        print("Thanks for using my tool")
                        time.sleep(3)
                        print("Please safely eject your USB before unplugging!")
                        break
                    else:
                        print("Folder not found")
                        break
                else:
                    print("Cancelled...")
                    break
            else:
                print("Invalid disk number. Try again.")
        except Exception as e:
            print(f"Error: {e}")

# Format option
def about():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""
ISOFORGE BOOTLOADER

DEVELOPER: IMJCDEV
VERSION: 1.0

INSTALLATION:
Step 1: Open "main.exe" as administrator
Step 2: Select option 1 and enter
Step 3: Enter the device "Disk number" and enter "Y" to continue
Step 4: Enter the "Assign Letter" of the 1st Partition of the USB or the Partition that has a label of "ISOFORGE"
Step 5: Open 2nd Partition of the USB or the Partition that has a label of "STORAGE". 
Step 6: Create a folder for your OS files (e.g. "ISOs") to make it more organized

Note: Dont edit or delete the boot/ folder of ISOFORGE Partition

GitHub: https://github.com/T3rr8us-P4nk/ISOForge-Bootloader
Facebook: https://www.facebook.com/T3rr8usP4nk/
          
YouTube Tutorial: 
          
THANK YOU FOR USING MY TOOL :)
""")

# User choices/options
def options():
    while True:
        choices = """
Options: 
1. Set-up IsoForge Bootloader
2. About
3. Exit
"""
        print(choices)
        try:
            user_choice = int(input("Enter Option: "))
            if user_choice == 1:
                set_up()
            elif user_choice == 2:
                about()
            elif user_choice == 3:
                break
            else:
                print(f"Option: {user_choice} not found")
        except:
            print("Error please try again")


os.system('cls' if os.name == 'nt' else 'clear')
banner()
options()