// File: frontend/src/App.js

// FIX: Removed 'import React' as it's not explicitly used and can cause build errors.
import { useState } from 'react'; 
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import './App.css';

const CUISINE_OPTIONS = ['Indian (General)', 'North Indian', 'South Indian', 'Chinese', 'Italian', 'Continental', 'Maharashtrian', 'Mughlai', 'Beverages', 'Desserts', 'Other'];
const FOOD_TYPE_OPTIONS = ['Veg', 'Non-Veg'];

function App() {
  const [selectedCuisines, setSelectedCuisines] = useState([]);
  const [selectedFoodTypes, setSelectedFoodTypes] = useState([]);
  const [priceRange, setPriceRange] = useState([100, 1000]);
  const [recommendations, setRecommendations] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCheckboxChange = (value, type) => {
    const updater = (prev) => prev.includes(value) ? prev.filter(item => item !== value) : [...prev, value];
    if (type === 'cuisine') setSelectedCuisines(updater);
    else setSelectedFoodTypes(updater);
  };

  const handleSuggestClick = async () => {
    setIsLoading(true);
    setError('');
    setRecommendations(null);

    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cuisines: selectedCuisines,
          foodTypes: selectedFoodTypes,
          minPrice: priceRange[0],
          maxPrice: priceRange[1]
        })
      });

      if (!response.ok) {
        throw new Error(`Network response was not ok. Status: ${response.status}`);
      }

      const data = await response.json();
      setRecommendations(data);

    } catch (err) {
      setError('Failed to fetch recommendations. Please check the Vercel logs.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <header><h1>Kya Khaega?</h1><p>Let us help you decide what to eat in Pune!</p></header>
      <div className="selection-panel">
        <fieldset><legend>Select Cuisine(s)</legend>{CUISINE_OPTIONS.map(c => (<label key={c}><input type="checkbox" value={c} onChange={()=>handleCheckboxChange(c, 'cuisine')}/>{c}</label>))}</fieldset>
        <fieldset><legend>Select Food Type(s)</legend>{FOOD_TYPE_OPTIONS.map(ft => (<label key={ft}><input type="checkbox" value={ft} onChange={()=>handleCheckboxChange(ft, 'foodType')}/>{ft}</label>))}</fieldset>
        <fieldset><legend>Price Range</legend><div className="price-slider-container"><div className="price-display">₹{priceRange[0]} - ₹{priceRange[1]}</div>
        <Slider 
            range 
            min={0} 
            max={2000} 
            // FIX: Use 'value' instead of 'defaultValue' for a fully controlled component.
            value={priceRange} 
            onChange={(newRange) => setPriceRange(newRange)} 
            allowCross={false} 
            step={50}
        />
        </div></fieldset>
      </div>
      <button onClick={handleSuggestClick} disabled={isLoading}>{isLoading ? 'Thinking...':'Find Me Food!'}</button>
      <div className="results-panel">
        {error && <p className="error-message">{error}</p>}
        {recommendations && recommendations.length > 0 && (<ul>{recommendations.map((item, index) => (<li key={index}><span className="item-name">{item.Item_Name}</span><span className="restaurant-name">at {item.Restaurant_Name}</span>{item.Price && <span className="price-tag">₹{Math.round(item.Price)}</span>}<span className="tags">{item['Food Type']} | {item.Cuisine}</span></li>))}</ul>)}
        {recommendations && recommendations.length === 0 && (<p className="no-results">No results found. Try different filters!</p>)}
      </div>
    </div>
  );
}
export default App;