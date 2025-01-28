import time, os

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class Console:
    def __init__(self) -> None:
        self.messageLimit: int = 25
        self.messages: list[str] = []
        self.intensive_logging_banner: bool = True
        self.columns, self.rows = os.get_terminal_size(0)

    def getPrefix(self) -> str:
        return f"[{time.strftime('%X')}]"

    def newLine(self, count: int = 1) -> None:
        for i in range(count):
            print("")

    def addMessage(self, message: str, extra: str = "") -> None:
        if extra != "": extra = f'{extra}] - '
        msg = f"{extra + self.getPrefix():25} {message}"
        print(len(self.messages))

        if(len(self.messages) >= self.messageLimit): self.messages.pop(0) # remove oldest message
        self.messages.append(msg)

        self.refresh()

    def log(self, message: str) -> None:
        self.addMessage(message)

    def error(self, message: str) -> None:
        self.addMessage(message + color.END, f"{color.RED}[ERROR")

    def warning(self, message: str) -> None:
        self.addMessage(message + color.END, f"{color.YELLOW}[WARNING")

    def warn(self, message: str) -> None:
        self.warning(message)

    def messageFromServer(self, message: str) -> None:
        self.addMessage(message, "[SERVER")

    def messageFromClient(self, message: str) -> None:
        self.addMessage(message, "[CLIENT")

    def printMessages(self) -> None:
        for m in self.messages:
            print(m)

    def clear(self) -> None:
        os.system("clear")

    def setIntensiveLogging(self, intensive_logging: bool):
        self.intensive_logging_banner = intensive_logging

    def refresh(self) -> None:
        self.clear()

        if self.intensive_logging_banner:
            for x in range(int(self.columns/2)-1): print(" ",end="")
            print(color.BOLD + "INTESIVE LOGGING" + color.END)

        self.printMessages()
