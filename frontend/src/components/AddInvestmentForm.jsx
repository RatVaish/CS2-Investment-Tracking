import {useState} from "react";
import {investmentAPI} from "../api/investments";

function AddInvestmentFrom({ onInvestmentAdded }) {
    const [formData, setFormData] = useState({
        item_name: "",
        item_type: "sticker",
        purchase_price: "",
        quantity: 1,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const itemTypes = [
        'skin', 'sticker', 'case', 'agent', 'knife',
        'gloves', 'patch', 'music_kit', 'graffiti', 'other'
    ];

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: name === "purchase_price" || name === "quantity"
             ? parseFloat(value) || ""
             : value
        }));
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      setError(null);

      try {
        // Ensure numbers are properly formatted
        const dataToSend = {
          ...formData,
          purchase_price: parseFloat(formData.purchase_price),
          quantity: parseInt(formData.quantity, 10)
        };

        console.log('Sending data:', dataToSend); // Debug log

        await investmentAPI.create(dataToSend);

        // Reset form
        setFormData({
          item_name: '',
          item_type: 'sticker',
          purchase_price: '',
          quantity: 1,
        });

        // Notify parent component
        onInvestmentAdded();
      } catch (err) {
        console.error('Error creating investment:', err); // Debug log
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="txt-xl font-semibold mb-4">Add New Investment</h2>

            {error && (
                <div className="bg-red-100 border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm front medium mb-1">
                        Item Name
                    </label>
                    <input
                        type="text"
                        name="item_name"
                        value={formData.item_name}
                        onChange={handleChange}
                        required
                        placeholder="e.g., Sticker | Katowice 2014 Tital (Holo)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1">
                        Item Type
                    </label>
                    <select
                        name="item_type"
                        value={formData.item_type}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {itemTypes.map(type => (
                            <option key={type} value={type}>
                                {type.charAt(0).toUpperCase() + type.slice(1).replace("_", " ")}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Purchase Price (£)
                        </label>
                        <input
                            type="number"
                            name="purchase_price"
                            value={formData.purchase_price}
                            onChange={handleChange}
                            required
                            min="0"
                            step="0.01"
                            placeholder="0.00"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Quantity
                        </label>
                        <input
                            type="number"
                            name="quantity"
                            value={formData.quantity}
                            onChange={handleChange}
                            required
                            min="1"
                            placeholder="1"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-md font-medium hover:bg-blue-700 active:bg-blue-800 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {loading ? 'Adding...' : '+ Add Investment'}
                </button>
            </form>
        </div>
    );
}

export default AddInvestmentFrom;
