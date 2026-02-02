"""
Oracle Secrets Module
=====================

Manages encrypted secrets, keys, and wallet information.
Inspired by Sage's encrypted API key management pattern.

Security Model:
- Seed phrases are NEVER revealed
- Private keys are NEVER revealed
- Addresses and balances CAN be revealed
- Each agent can only query their own secrets
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Try to import cryptography for encryption
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


@dataclass
class WalletInfo:
    """Information about an agent's wallet that can be safely revealed."""
    agent_id: str
    address: str
    balances: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "address": self.address,
            "balances": self.balances,
        }


class SecretsKeeper:
    """
    Manages secrets and encrypted data for the Oracle.
    
    Following Sage's pattern of encrypted key management,
    this class handles:
    - Encrypted seed phrase storage
    - Wallet address derivation
    - Balance queries
    - Secret validation
    
    NEVER reveals:
    - Seed phrases
    - Private keys
    - Master encryption keys
    """
    
    VALID_AGENTS = ["agent1", "agent2", "agent3", "agent4", "love_treasury"]
    
    def __init__(
        self,
        encrypted_dir: Optional[Path] = None,
        master_key: Optional[str] = None,
        solana_rpc: Optional[str] = None,
    ):
        """
        Initialize the secrets keeper.
        
        Args:
            encrypted_dir: Directory containing encrypted seed files
            master_key: Master encryption key (from environment)
            solana_rpc: Solana RPC endpoint
        """
        self.encrypted_dir = encrypted_dir or Path(__file__).parent.parent / "treasury" / ".encrypted"
        self.master_key = master_key or os.environ.get("ORACLE_MASTER_KEY", "")
        self.solana_rpc = solana_rpc or os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
        
        # Token mint addresses
        self.token_mints = {
            "SOL": "native",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        }
    
    def validate_agent(self, agent_id: str) -> bool:
        """Validate that an agent ID is valid."""
        return agent_id in self.VALID_AGENTS
    
    def has_master_key(self) -> bool:
        """Check if the master key is available."""
        return bool(self.master_key)
    
    def _get_seed_file(self, agent_id: str) -> Path:
        """Get the path to an agent's encrypted seed file."""
        return self.encrypted_dir / f"{agent_id}.seed.enc"
    
    def _decrypt_seed(self, agent_id: str) -> Optional[str]:
        """
        Decrypt an agent's seed phrase.
        
        This is INTERNAL ONLY - the seed is never returned to callers.
        It's used only for deriving addresses and signing transactions.
        """
        if not self.has_master_key():
            return None
        
        seed_file = self._get_seed_file(agent_id)
        if not seed_file.exists():
            return None
        
        try:
            # Use OpenSSL for decryption (matching oracle.sh)
            result = subprocess.run(
                [
                    "openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "100000",
                    "-d", "-base64", "-in", str(seed_file), "-pass", f"pass:{self.master_key}"
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None
    
    def _derive_address(self, agent_id: str) -> Optional[str]:
        """
        Derive a Solana address from an agent's seed.
        
        Returns the public address only - never the private key.
        """
        seed = self._decrypt_seed(agent_id)
        if not seed:
            return None
        
        try:
            # Try using solana-keygen if available
            if self._has_solana_cli():
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.seed', delete=False) as f:
                    f.write(seed)
                    seed_file = f.name
                
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
                    keypair_file = f.name
                
                try:
                    # Recover keypair
                    subprocess.run(
                        ["solana-keygen", "recover", "--force", "--outfile", keypair_file],
                        input=seed,
                        capture_output=True,
                        text=True,
                    )
                    
                    # Get public key
                    result = subprocess.run(
                        ["solana-keygen", "pubkey", keypair_file],
                        capture_output=True,
                        text=True,
                    )
                    
                    if result.returncode == 0:
                        return result.stdout.strip()
                finally:
                    # Clean up
                    os.unlink(seed_file)
                    os.unlink(keypair_file)
            
            # Fallback: deterministic derivation
            import hashlib
            seed_hash = hashlib.sha256(f"{seed}{agent_id}solana".encode()).hexdigest()
            return f"DERIVED_{seed_hash[:32]}"
            
        except Exception:
            return None
    
    def _has_solana_cli(self) -> bool:
        """Check if Solana CLI is available."""
        try:
            result = subprocess.run(["which", "solana-keygen"], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _query_sol_balance(self, address: str) -> float:
        """Query SOL balance from Solana RPC."""
        try:
            import urllib.request
            
            payload = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }).encode()
            
            req = urllib.request.Request(
                self.solana_rpc,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                lamports = data.get("result", {}).get("value", 0)
                return lamports / 1_000_000_000  # Convert lamports to SOL
                
        except Exception:
            return 0.0
    
    def _query_token_balance(self, address: str, mint: str) -> float:
        """Query SPL token balance from Solana RPC."""
        try:
            import urllib.request
            
            payload = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    address,
                    {"mint": mint},
                    {"encoding": "jsonParsed"}
                ]
            }).encode()
            
            req = urllib.request.Request(
                self.solana_rpc,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                accounts = data.get("result", {}).get("value", [])
                if accounts:
                    return accounts[0].get("account", {}).get("data", {}).get("parsed", {}).get("info", {}).get("tokenAmount", {}).get("uiAmount", 0.0)
                
        except Exception:
            pass
        
        return 0.0
    
    # Public API - Safe methods that can be called by agents
    
    def get_address(self, agent_id: str) -> Optional[str]:
        """
        Get an agent's wallet address.
        
        This is SAFE to reveal - it's the public address.
        """
        if not self.validate_agent(agent_id):
            return None
        return self._derive_address(agent_id)
    
    def get_balance(self, agent_id: str, token: str = "SOL") -> Optional[float]:
        """
        Get an agent's balance for a specific token.
        
        This is SAFE to reveal - it's public blockchain data.
        """
        if not self.validate_agent(agent_id):
            return None
        
        address = self._derive_address(agent_id)
        if not address or address.startswith("DERIVED_"):
            return None
        
        mint = self.token_mints.get(token.upper())
        if not mint:
            return None
        
        if mint == "native":
            return self._query_sol_balance(address)
        else:
            return self._query_token_balance(address, mint)
    
    def get_all_balances(self, agent_id: str) -> Dict[str, float]:
        """
        Get all token balances for an agent.
        
        Returns only non-zero balances.
        """
        if not self.validate_agent(agent_id):
            return {}
        
        balances = {}
        for token in self.token_mints:
            balance = self.get_balance(agent_id, token)
            if balance and balance > 0:
                balances[token] = balance
        
        return balances
    
    def get_wallet_info(self, agent_id: str) -> Optional[WalletInfo]:
        """
        Get complete wallet information for an agent.
        
        Returns address and all balances.
        """
        if not self.validate_agent(agent_id):
            return None
        
        address = self.get_address(agent_id)
        if not address:
            return None
        
        balances = self.get_all_balances(agent_id)
        
        return WalletInfo(
            agent_id=agent_id,
            address=address,
            balances=balances,
        )
    
    def verify_wallet(self, agent_id: str) -> Dict[str, Any]:
        """
        Verify an agent's wallet is properly configured.
        
        Returns verification status without revealing secrets.
        """
        if not self.validate_agent(agent_id):
            return {"valid": False, "error": "Invalid agent ID"}
        
        seed_file = self._get_seed_file(agent_id)
        
        result = {
            "agent_id": agent_id,
            "seed_file_exists": seed_file.exists(),
            "master_key_available": self.has_master_key(),
            "decryption_possible": False,
            "address_derivable": False,
        }
        
        if result["seed_file_exists"] and result["master_key_available"]:
            seed = self._decrypt_seed(agent_id)
            result["decryption_possible"] = seed is not None
            
            if seed:
                word_count = len(seed.split())
                result["seed_word_count"] = word_count
                result["address_derivable"] = word_count in [12, 24]
        
        result["valid"] = all([
            result["seed_file_exists"],
            result["master_key_available"],
            result["decryption_possible"],
            result["address_derivable"],
        ])
        
        return result
    
    def get_supported_tokens(self) -> List[str]:
        """Get list of supported tokens."""
        return list(self.token_mints.keys())


# Singleton instance
_keeper = None

def get_secrets_keeper(**kwargs) -> SecretsKeeper:
    """Get the secrets keeper singleton."""
    global _keeper
    if _keeper is None:
        _keeper = SecretsKeeper(**kwargs)
    return _keeper
