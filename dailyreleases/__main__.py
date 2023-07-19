"""
The main terminal-based entry point. Invoke as `dailyreleases' or `python3 -m dailyreleases'.
"""

if __name__ == "__main__":
    from .main import main
#    from .stores import epic
    main()
    #epic.search("Gravity Circuit")
