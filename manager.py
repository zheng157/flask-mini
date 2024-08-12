from application import manager,app
from flask_script import Server
import www
from jobs.launcher import runJob

manager.add_command("runserver",Server(host='0.0.0.0',port=app.config['SERVER_POET'],use_debugger= True))

# job entrance
manager.add_command('runjob',runJob())

def main():
    manager.run()

if __name__ == '__main__':
    try:
        import sys
        sys.exit(main())
    except Exception as e:
        import traceback
        traceback.print_exc()

