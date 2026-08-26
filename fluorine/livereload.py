import subprocess, sys, time


def liveReload(path: str) -> None:
    if "--livereload" in sys.argv:
        old_content: str = ""
        while True:
            with open(path) as file:
                content: str = file.read()
            if content != old_content:
                args: list[str] = sys.argv[1:]
                if "--livereload" in args:
                    args.remove("--livereload")
                if "--lrsilent" not in args:
                    print("fluorine.livereload: Reloading program...")
                subprocess.run([sys.executable, path, *args])
            old_content = content
            time.sleep(0.1)