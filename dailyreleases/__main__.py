"""
The main terminal-based entry point. Invoke as `dailyreleases' or `python3 -m dailyreleases'.
"""

if __name__ == "__main__":
    from .main import Main
#    from .stores import epic
    Main().run_main()
    #epic.search("Gravity Circuit")
