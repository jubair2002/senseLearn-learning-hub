# SenseLearn

E-learning education system for students with disabilities in Bangladesh.

---

## Prerequisites

Ensure you have the following installed on your system before proceeding:

- **Python 3.8+**
- **Git**
- **pip** (usually bundled with Python)

### Check your versions

```bash
python --version
pip --version
git --version
```

---

## Local Setup & Installation

Follow these steps carefully to get the project running on your machine.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-folder-name>
```

### 2. Create a Virtual Environment (Recommended)

This keeps your project dependencies organized and prevents conflicts.

**Create:**
```bash
python -m venv venv
```

**Activate:**
- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Additional Configuration

Some specific setup steps or custom run commands are stored in the `InstallCommand.txt` file. Please review them before launching:

```bash
# To view the file in your terminal:
cat InstallCommand.txt
```

**Note:** You can also simply open this file in any text editor.

---

## Running the Application

Once setup is complete, you can launch the application using:

```bash
python main.py
# or
python app.py
```

---

## Project Structure

```
project-root/
│
├── main.py                 # Entry point of the application
├── requirements.txt        # List of Python dependencies
├── InstallCommand.txt      # Extra setup instructions
├── venv/                   # Your isolated Python environment
└── README.md              # This file
```

---

## Contributing

We welcome contributions to SenseLearn! Here's how you can help:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---


## Support

If you encounter any issues or have questions, please open an issue on the repository.

---

**Built with dedication to make education accessible for all students in Bangladesh.**
