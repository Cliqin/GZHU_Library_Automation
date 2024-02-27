from schedule import mySchedule
import sys
sys.path.append("..")
from src.Shell import Shell

if __name__ == '__main__':
    Shell(mySchedule).Reserve()
