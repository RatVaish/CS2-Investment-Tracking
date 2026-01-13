function PortfolioSummary({ investments }) {
    if (!investments || !Array.isArray(investments) || investments.length === 0) {
        return null; // Don't render anything if no investments
    }

    const totalInvested = investments.reduce((sum, inv) =>
        sum + (inv.purchase_price * inv.quantity), 0
    );

    const totalItems = investments.reduce((sum, inv) =>
        sum + inv.quantity, 0
    );

    const typeBreakdown = investments.reduce((acc, inv) => {
        const type = inv.item_type;
        if (!acc[type]) {
            acc[type] = {count: 0, value: 0 };
        }
        acc[type].count +=  inv.quantity;
        acc[type].value += inv.purchase_price * inv.quantity;
        return acc;
    }, {});

    return (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Portfolio Summary</h2>            <div className="gird gird-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Total Invested</p>
                    <p className="text-2xl font-bold text-b;ue-600">
                        ${totalInvested.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                    </p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Total Items</p>
                    <p className="text-2xl font-bold text-green-600">
                        {totalItems}
                    </p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Unique Investments</p>
                    <p className="text-2xl font-bold text-purple-600">
                        {investments.length}
                    </p>
                </div>
            </div>

            {Object.keys(typeBreakdown).length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Breakdown by Type</h3>
                    <div className="grid grid-cold-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                        {Object.entries(typeBreakdown).map(([type, data]) => (
                            <div key={type} className="border border-gray-200 rounded-lg p-3">
                                <p className="text-xs text-gray-500 capitalize mb-1">
                                    {type.replace("_", " ")}
                                </p>
                                <p className="font-semibold text-sm">
                                    {data.count} item{data.count !== 1 ? "s" : " "}
                                </p>
                                <p className="text-xs text-gray-600">
                                    ${data.value.toLocaleString()}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default PortfolioSummary;
