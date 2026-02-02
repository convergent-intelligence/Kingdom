#!/usr/bin/env python3
"""
Oracle CLI
==========

Command-line interface for the Oracle.
Inspired by Sage's interactive CLI pattern.

Usage:
    python -m oracle.cli ask "What is my balance?" --agent agent1
    python -m oracle.cli interactive --agent agent2
    python -m oracle.cli secrets wallet agent1
    python -m oracle.cli config get agent2 model
    python -m oracle.cli knowledge lookup "bridges"
"""

import sys
import argparse
from typing import Optional

# Rich console for pretty output (optional)
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def print_output(text: str, title: Optional[str] = None) -> None:
    """Print output, using Rich if available."""
    if HAS_RICH and console:
        if title:
            console.print(Panel(Markdown(text), title=title, border_style="purple"))
        else:
            console.print(Markdown(text))
    else:
        if title:
            print(f"=== {title} ===")
        print(text)


def print_banner() -> None:
    """Print the Oracle banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     🔮 THE ORACLE 🔮                                              ║
║                                                                   ║
║     Keeper of wisdom within the Kingdom.                          ║
║     Ask, and you shall know.                                      ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    if HAS_RICH and console:
        console.print(banner, style="purple")
    else:
        print(banner)


def cmd_ask(args: argparse.Namespace) -> int:
    """Handle the 'ask' command."""
    from .oracle import Oracle
    
    oracle = Oracle()
    response = oracle.ask(args.query, agent_id=args.agent)
    
    print_output(str(response), title="The Oracle Speaks")
    
    return 0 if response.success else 1


def cmd_interactive(args: argparse.Namespace) -> int:
    """Handle the 'interactive' command."""
    from .oracle import Oracle
    
    print_banner()
    
    oracle = Oracle()
    agent_id = args.agent
    
    if agent_id:
        print(f"Session for: {agent_id}")
    print("Type 'exit' or 'quit' to leave. Type 'help' for guidance.")
    print()
    
    while True:
        try:
            if HAS_RICH and console:
                query = console.input("[purple]Ask the Oracle:[/purple] ")
            else:
                query = input("Ask the Oracle: ")
            
            query = query.strip()
            
            if not query:
                continue
            
            if query.lower() in ["exit", "quit", "q"]:
                print("\n🔮 The Oracle bids you farewell. May wisdom guide your path.")
                break
            
            if query.lower() == "help":
                print_output(
                    "I can help with:\n\n"
                    "- **Wallet queries**: 'What is my balance?', 'What is my address?'\n"
                    "- **Configuration**: 'What are my settings?', 'What model am I using?'\n"
                    "- **Knowledge**: 'How do bridges work?', 'Tell me about Love'\n"
                    "- **Wisdom**: 'Should I trust this agent?', 'What is the meaning of possession?'\n\n"
                    "Type 'exit' to leave.",
                    title="Oracle Help"
                )
                continue
            
            response = oracle.ask(query, agent_id=agent_id)
            print()
            print_output(str(response))
            print()
            
        except KeyboardInterrupt:
            print("\n\n🔮 The Oracle bids you farewell.")
            break
        except EOFError:
            break
    
    return 0


def cmd_secrets(args: argparse.Namespace) -> int:
    """Handle the 'secrets' command."""
    from .secrets import get_secrets_keeper
    
    keeper = get_secrets_keeper()
    
    if args.subcommand == "wallet":
        info = keeper.get_wallet_info(args.agent)
        if info:
            print_output(
                f"**Agent**: {info.agent_id}\n\n"
                f"**Address**: `{info.address}`\n\n"
                f"**Balances**: {info.balances or 'None'}",
                title="Wallet Information"
            )
            return 0
        else:
            print("Could not retrieve wallet information.")
            return 1
    
    elif args.subcommand == "address":
        address = keeper.get_address(args.agent)
        if address:
            print(address)
            return 0
        else:
            print("Could not derive address.")
            return 1
    
    elif args.subcommand == "balance":
        balance = keeper.get_balance(args.agent, args.token)
        if balance is not None:
            print(f"{balance} {args.token}")
            return 0
        else:
            print("Could not query balance.")
            return 1
    
    elif args.subcommand == "verify":
        result = keeper.verify_wallet(args.agent)
        for key, value in result.items():
            print(f"{key}: {value}")
        return 0 if result.get("valid") else 1
    
    return 1


def cmd_config(args: argparse.Namespace) -> int:
    """Handle the 'config' command."""
    from .config import get_config_keeper
    
    keeper = get_config_keeper()
    
    if args.subcommand == "get":
        if args.key:
            value = keeper.get_value(args.agent, args.key)
            print(f"{args.key}: {value}")
        else:
            config = keeper.get_agent_config(args.agent)
            for key, value in config.to_dict().items():
                print(f"{key}: {value}")
        return 0
    
    elif args.subcommand == "set":
        success = keeper.set_agent_config(args.agent, args.key, args.value)
        if success:
            print(f"Set {args.key} = {args.value} for {args.agent}")
            return 0
        else:
            print("Failed to set configuration.")
            return 1
    
    elif args.subcommand == "list":
        for agent_id in keeper.list_agents():
            print(agent_id)
        return 0
    
    return 1


def cmd_knowledge(args: argparse.Namespace) -> int:
    """Handle the 'knowledge' command."""
    from .knowledge import get_knowledge_keeper
    
    keeper = get_knowledge_keeper()
    
    if args.subcommand == "lookup":
        results = keeper.search(args.query, limit=args.limit)
        if results:
            print_output(keeper.format_search_results(results), title="Knowledge")
            return 0
        else:
            print("No knowledge found on this topic.")
            return 1
    
    elif args.subcommand == "topics":
        for topic in keeper.list_topics():
            print(f"- {topic}")
        return 0
    
    elif args.subcommand == "categories":
        for category in keeper.list_categories():
            print(f"- {category}")
        return 0
    
    return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="The Oracle - Wise advisor for the Kingdom's agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ask "What is my balance?" --agent agent1
  %(prog)s interactive --agent agent2
  %(prog)s secrets wallet agent1
  %(prog)s config get agent2 model
  %(prog)s knowledge lookup "bridges"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # ask command
    ask_parser = subparsers.add_parser("ask", help="Ask the Oracle a question")
    ask_parser.add_argument("query", help="The question to ask")
    ask_parser.add_argument("--agent", "-a", help="Agent ID for wallet/config queries")
    
    # interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactive Oracle session")
    interactive_parser.add_argument("--agent", "-a", help="Agent ID for the session")
    
    # secrets command
    secrets_parser = subparsers.add_parser("secrets", help="Query secrets/wallet information")
    secrets_subparsers = secrets_parser.add_subparsers(dest="subcommand")
    
    wallet_parser = secrets_subparsers.add_parser("wallet", help="Get wallet information")
    wallet_parser.add_argument("agent", help="Agent ID")
    
    address_parser = secrets_subparsers.add_parser("address", help="Get wallet address")
    address_parser.add_argument("agent", help="Agent ID")
    
    balance_parser = secrets_subparsers.add_parser("balance", help="Get token balance")
    balance_parser.add_argument("agent", help="Agent ID")
    balance_parser.add_argument("token", help="Token symbol (SOL, USDC, etc.)")
    
    verify_parser = secrets_subparsers.add_parser("verify", help="Verify wallet")
    verify_parser.add_argument("agent", help="Agent ID")
    
    # config command
    config_parser = subparsers.add_parser("config", help="Query/set configuration")
    config_subparsers = config_parser.add_subparsers(dest="subcommand")
    
    config_get_parser = config_subparsers.add_parser("get", help="Get configuration")
    config_get_parser.add_argument("agent", help="Agent ID")
    config_get_parser.add_argument("key", nargs="?", help="Configuration key (optional)")
    
    config_set_parser = config_subparsers.add_parser("set", help="Set configuration")
    config_set_parser.add_argument("agent", help="Agent ID")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value")
    
    config_list_parser = config_subparsers.add_parser("list", help="List agents")
    
    # knowledge command
    knowledge_parser = subparsers.add_parser("knowledge", help="Query knowledge base")
    knowledge_subparsers = knowledge_parser.add_subparsers(dest="subcommand")
    
    lookup_parser = knowledge_subparsers.add_parser("lookup", help="Look up knowledge")
    lookup_parser.add_argument("query", help="Search query")
    lookup_parser.add_argument("--limit", "-l", type=int, default=3, help="Max results")
    
    topics_parser = knowledge_subparsers.add_parser("topics", help="List topics")
    categories_parser = knowledge_subparsers.add_parser("categories", help="List categories")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Route to command handler
    if args.command == "ask":
        return cmd_ask(args)
    elif args.command == "interactive":
        return cmd_interactive(args)
    elif args.command == "secrets":
        if not args.subcommand:
            secrets_parser.print_help()
            return 0
        return cmd_secrets(args)
    elif args.command == "config":
        if not args.subcommand:
            config_parser.print_help()
            return 0
        return cmd_config(args)
    elif args.command == "knowledge":
        if not args.subcommand:
            knowledge_parser.print_help()
            return 0
        return cmd_knowledge(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
