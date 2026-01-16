"""
Cliente da API PumpPortal
"""
import aiohttp
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class BuyResult:
    """Resultado de uma tentativa de compra"""
    success: bool
    attempt: int
    elapsed_ms: float
    response: Dict[str, Any]
    signature: Optional[str] = None
    error: Optional[str] = None


class PumpPortalAPI:
    """Cliente para API PumpPortal"""

    BASE_URL = "https://pumpportal.fun/api/trade"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def buy(
        self,
        mint: str,
        amount: float,
        slippage: int = 49,
        priority_fee: float = 0.1,
        pool: str = "auto"
    ) -> BuyResult:
        """Executa uma compra"""
        url = f"{self.BASE_URL}?api-key={self.api_key}"

        payload = {
            "action": "buy",
            "mint": mint,
            "amount": amount,
            "denominatedInSol": "true",
            "slippage": slippage,
            "priorityFee": priority_fee,
            "pool": pool
        }

        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    elapsed = (time.time() - start_time) * 1000

                    if "signature" in result:
                        return BuyResult(
                            success=True,
                            attempt=1,
                            elapsed_ms=elapsed,
                            response=result,
                            signature=result["signature"]
                        )
                    else:
                        return BuyResult(
                            success=False,
                            attempt=1,
                            elapsed_ms=elapsed,
                            response=result,
                            error=result.get("error", "Unknown error")
                        )

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return BuyResult(
                success=False,
                attempt=1,
                elapsed_ms=elapsed,
                response={},
                error=str(e)
            )

    async def buy_multiple(
        self,
        mint: str,
        amount: float,
        slippage: int = 49,
        priority_fee: float = 0.1,
        num_attempts: int = 5,
        delay_between: float = 0.5,
        on_result: Optional[Callable[[BuyResult], None]] = None
    ) -> list:
        """Executa multiplas tentativas de compra"""
        import asyncio

        results = []

        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}?api-key={self.api_key}"

            for i in range(num_attempts):
                payload = {
                    "action": "buy",
                    "mint": mint,
                    "amount": amount,
                    "denominatedInSol": "true",
                    "slippage": slippage,
                    "priorityFee": priority_fee,
                    "pool": "auto"
                }

                start_time = time.time()

                try:
                    async with session.post(url, json=payload) as resp:
                        response = await resp.json()
                        elapsed = (time.time() - start_time) * 1000

                        if "signature" in response:
                            result = BuyResult(
                                success=True,
                                attempt=i + 1,
                                elapsed_ms=elapsed,
                                response=response,
                                signature=response["signature"]
                            )
                        else:
                            result = BuyResult(
                                success=False,
                                attempt=i + 1,
                                elapsed_ms=elapsed,
                                response=response,
                                error=response.get("error", "Unknown error")
                            )

                except Exception as e:
                    elapsed = (time.time() - start_time) * 1000
                    result = BuyResult(
                        success=False,
                        attempt=i + 1,
                        elapsed_ms=elapsed,
                        response={},
                        error=str(e)
                    )

                results.append(result)

                if on_result:
                    on_result(result)

                if i < num_attempts - 1:
                    await asyncio.sleep(delay_between)

        return results
