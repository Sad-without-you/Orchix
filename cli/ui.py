from rich.console import Console
from rich.panel import Panel
import inquirer
import os

console = Console()


def clear_screen():
    '''Clear terminal screen'''
    os.system('cls' if os.name == 'nt' else 'clear')

def show_success(message):
    '''Show success message in green'''
    
    console.print(f"✅ {message}", style="bold green")

def show_error(message):
    '''Show error message in red'''
    
    console.print(f"❌ {message}", style="bold red")  

def show_warning(message):
    '''Show warning message in yellow'''
    
    console.print(f"⚠ {message}", style="yellow")

def show_info(message):
    '''Show info message in blue'''
    
    console.print(f"ℹ {message}", style="bold blue")

def show_panel(title, content, style="cyan"):
    '''Show content in a panel with border'''
    clear_screen()

    # Persistent ORCHIX header
    console.print(Panel(
        "[bold cyan]ORCHIX v1.1[/bold cyan]\n[dim]DevOps Container Management System[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))

    panel = Panel(
        content,
        title=title,
        border_style=style
    )
    console.print(panel)

def show_step(message, status="done"):
    '''Show a progress step with vertical connecting line.
    status: "done", "active", "error"
    '''
    icons = {"done": "✅", "active": "⏳", "error": "❌"}
    styles = {"done": "bold green", "active": "bold cyan", "error": "bold red"}
    icon = icons.get(status, "•")
    style = styles.get(status, "white")
    console.print(f"  │", style="dim cyan")
    console.print(f"  ├── {icon} {message}", style=style)

def show_step_final(message, success=True):
    '''Show the final step (uses end connector)'''
    if success:
        console.print(f"  │", style="dim cyan")
        console.print(f"  └── ✅ {message}", style="bold green")
    else:
        console.print(f"  │", style="dim cyan")
        console.print(f"  └── ❌ {message}", style="bold red")

def show_step_detail(message):
    '''Show a detail line under a step, maintaining the vertical line'''
    console.print(f"  │     {message}", style="dim green")

def show_step_line():
    '''Show just the vertical connecting line'''
    console.print(f"  │", style="dim cyan")

def step_input(prompt):
    '''Input with vertical line prefix for connected config flow'''
    console.print(f"  │", style="dim cyan", end="")
    return input(f"     {prompt}")

def show_result_panel(content, title="Success"):
    '''Show result info in a styled panel'''
    panel = Panel(
        content,
        title=f"[bold green]{title}[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print()
    console.print(panel)

def select_from_list(message, choices):
    '''Interactive list selection (for menus without step line)'''
    questions = [
        inquirer.List(
            'selection',
            message=message,
            choices=choices
        )
    ]

    answer = inquirer.prompt(questions)
    return answer['selection']

def step_select(message, choices):
    '''Numbered selection with vertical line prefix for connected config flow'''
    console.print(f"  │", style="dim cyan")
    console.print(f"  │     [bold cyan]{message}:[/bold cyan]")
    for i, choice in enumerate(choices, 1):
        console.print(f"  │       {i}) {choice}", style="dim green")

    while True:
        console.print(f"  │", style="dim cyan", end="")
        selection = input(f"     Select [1-{len(choices)}]: ").strip()
        try:
            idx = int(selection)
            if 1 <= idx <= len(choices):
                return choices[idx - 1]
        except ValueError:
            pass
        console.print(f"  │     Please enter 1-{len(choices)}", style="dim red")