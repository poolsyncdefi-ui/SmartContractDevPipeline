"use client";

export default function DeFiComposer() {
    return (
        <>
        <div class="glass-card p-6">
            <h3 class="text-lg font-bold mb-4">🧩 DeFi Composer</h3>
            <p class="text-sm text-gray-400 mb-6">Glisse et dépose pour créer ta stratégie</p>
            
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-blue-500/50">
                    <span class="text-sm">💰 Deposit</span>
                    <p class="text-xs text-gray-400 mt-1">USDC • 1000$</p>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-purple-500/50">
                    <span class="text-sm">🏊‍♂️ Stake</span>
                    <p class="text-xs text-gray-400 mt-1">Aave • 3.2% APY</p>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-green-500/50">
                    <span class="text-sm">🔄 Swap</span>
                    <p class="text-xs text-gray-400 mt-1">ETH → DAI</p>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-dashed border-yellow-500/50">
                    <span class="text-sm">⚡ Leverage</span>
                    <p class="text-xs text-gray-400 mt-1">2x • 8.5% APY</p>
                </div>
            </div>
            
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-xl">
                <div>
                    <p class="text-sm font-medium">Rendement estimé</p>
                    <p class="text-2xl font-bold text-green-400">+12.4% APY</p>
                </div>
                <button class="px-6 py-2 bg-blue-600 rounded-lg">
                    Exécuter
                </button>
            </div>
        </div>
        </>
    );
}
