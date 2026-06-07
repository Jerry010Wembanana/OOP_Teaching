# Installing Pybricks for PyCharm or VS Code

## Goal

This guide explains how to install the tools needed to write and run Pybricks code from either PyCharm or VS Code.

We will install:

1. Pybricks firmware on the LEGO hub
2. Python on the computer
3. `pybricksdev` on the computer

`pybricksdev` is the tool that sends the Python code from the computer to the LEGO hub.

---

# Part 1: Install Pybricks Firmware on the LEGO Hub

## Step 1: Open Pybricks Code

Open Chrome or Edge.

Go to:

```text
https://code.pybricks.com
```

## Step 2: Connect the LEGO Hub

Turn on the LEGO hub.

In Pybricks Code, connect to the hub using Bluetooth.

## Step 3: Install Pybricks Firmware

In Pybricks Code:

1. Open the tools menu.
2. Choose **Install Pybricks firmware**.
3. Select the correct hub type.
4. Follow the instructions on the screen.
5. Wait until the installation is finished.

After this step, the LEGO hub can run Pybricks programs.

---

# Part 2: Install Python on the Computer

Pybricksdev requires Python to be installed on the computer.

## Step 1: Check Whether Python Is Installed

Open Command Prompt, PowerShell, Terminal, PyCharm Terminal, or VS Code Terminal.

Run:

```bash
python --version
```

On Windows, this may also work:

```bash
py --version
```

You should see something like:

```text
Python 3.10.x
```

or newer.

## Step 2: Install Python if Needed

If Python is not installed, download it from:

```text
https://www.python.org/downloads/
```

During installation, make sure to check:

```text
Add Python to PATH
```

This is important because it allows the computer to recognize the `python` command.

---

# Part 3: Install pybricksdev

Open Command Prompt, PowerShell, Terminal, PyCharm Terminal, or VS Code Terminal.

Run:

```bash
python -m pip install pybricksdev
```

On Windows, if that command does not work, try:

```bash
py -m pip install pybricksdev
```

---

# Part 4: Check Whether pybricksdev Installed Correctly

Run:

```bash
pybricksdev --help
```

If a help message appears, the installation worked.

If the command is not recognized, try:

```bash
python -m pybricksdev --help
```

or on Windows:

```bash
py -m pybricksdev --help
```

---

# Part 5: Run a Pybricks Program

After Pybricks firmware and `pybricksdev` are installed, you can run a Python file on the LEGO hub.

Make sure:

1. The LEGO hub is turned on.
2. The hub has Pybricks firmware installed.
3. Your Python file is saved.
4. You are in the same folder as the Python file in the terminal.

For a file named `main.py`, run:

```bash
pybricksdev run ble main.py
```

This sends `main.py` to the LEGO hub and runs it.

---

# Part 6: Run Code on a Specific Hub

If there are multiple LEGO hubs nearby, use the hub name.

```bash
pybricksdev run ble --name "Your Hub Name" main.py
```

Replace:

```text
Your Hub Name
```

with the actual name of the hub.

Example:

```bash
pybricksdev run ble --name "Hub_01" main.py
```

---

# Part 7: Test Program

Create or open a file named:

```text
main.py
```

Copy this code into it:

```python
from pybricks.hubs import PrimeHub
from pybricks.tools import wait

hub = PrimeHub()

hub.speaker.beep()
wait(1000)
```

Then run:

```bash
pybricksdev run ble main.py
```

If the hub beeps, the setup is working.

---

# Part 8: Common Issues

## Problem: `python` is not recognized

Try:

```bash
py --version
```

If `py` works, use:

```bash
py -m pip install pybricksdev
```

instead of:

```bash
python -m pip install pybricksdev
```

---

## Problem: `pybricksdev` is not recognized

Try:

```bash
python -m pybricksdev --help
```

or:

```bash
py -m pybricksdev --help
```

You can also reinstall it:

```bash
python -m pip install --upgrade pybricksdev
```

or:

```bash
py -m pip install --upgrade pybricksdev
```

---

## Problem: Hub Does Not Connect

Try these steps:

1. Make sure the hub is turned on.
2. Make sure Bluetooth is enabled.
3. Close the LEGO SPIKE app.
4. Close Pybricks Code if it is already connected to the hub.
5. Restart the hub.
6. Run the command again:

```bash
pybricksdev run ble main.py
```

---

## Problem: Multiple Hubs Are Nearby

Use the hub name:

```bash
pybricksdev run ble --name "Your Hub Name" main.py
```

Example:

```bash
pybricksdev run ble --name "Hub_01" main.py
```

---

# Quick Command Summary

## Install pybricksdev

```bash
python -m pip install pybricksdev
```

or:

```bash
py -m pip install pybricksdev
```

## Check pybricksdev

```bash
pybricksdev --help
```

## Run a Program

```bash
pybricksdev run ble main.py
```

## Run on a Specific Hub

```bash
pybricksdev run ble --name "Your Hub Name" main.py
```

---

# Final Check

The setup is complete when:

1. Pybricks firmware is installed on the LEGO hub.
2. Python is installed on the computer.
3. `pybricksdev` is installed.
4. The command below runs successfully:

```bash
pybricksdev run ble main.py
```
