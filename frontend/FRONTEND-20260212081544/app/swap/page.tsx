'use client';

export default function SwapPage() {
    return (
        <>
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Swap - FullSuite</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full bg-gray-800/50 rounded-2xl p-8 border border-gray-700">
            <h1 class="text-2xl font-bold mb-6 text-center">Swap Tokens</h1>
            <div class="space-y-4">
                <div class="bg-gray-700/50 rounded-xl p-4">
                    <div class="flex justify-between mb-2">
                        <label class="text-sm text-gray-400">From</label>
                        <span class="text-sm text-gray-400">Balance: 10.5 ETH</span>
                    </div>
                    <div class="flex space-x-2">
                        <input type="number" placeholder="0.0" 
                               class="flex-1 bg-transparent text-2xl outline-none" value="1.0">
                        <select class="bg-gray-600 rounded-lg px-3 py-2">
                            <option>ETH</option>
                            <option>USDC</option>
                        </select>
                    </div>
                </div>
                <div class="flex justify-center">
                    <div class="bg-gray-700 rounded-full p-2">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
                        </svg>
                    </div>
                </div>
                <div class="bg-gray-700/50 rounded-xl p-4">
                    <div class="flex justify-between mb-2">
                        <label class="text-sm text-gray-400">To</label>
                        <span class="text-sm text-gray-400">Balance: 0.5 BTC</span>
                    </div>
                    <div class="flex space-x-2">
                        <input type="number" placeholder="0.0" 
                               class="flex-1 bg-transparent text-2xl outline-none" value="0.05" readonly>
                        <select class="bg-gray-600 rounded-lg px-3 py-2">
                            <option>BTC</option>
                            <option>ETH</option>
                        </select>
                    </div>
                </div>
                <button class="w-full gradient-bg text-white font-bold py-4 px-6 rounded-xl 
                             hover:opacity-90 transition transform hover:scale-[1.02]">
                    Swap
                </button>
            </div>
        </div>
    </div>
</body>
</html>
        </>
    );
}
