import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plane, Train, Bus, Hotel, Search, AlertTriangle, RefreshCw, MapPin, DollarSign, Clock, Star, Map as MapIcon, Briefcase, ExternalLink, X, Cloud, CloudRain, Sun, TrendingUp, TrendingDown, Brain } from 'lucide-react';
import { planTrip, updatePlan, getTrending, getOffers, searchTransport, searchHotels, getMyTrips, predictPrice, getLstmModelInfo } from './api';
import MapWidget from './components/MapWidget';
import './index.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<any | null>(null);
  const [trending, setTrending] = useState<any[]>([]);
  const [offers, setOffers] = useState<any[]>([]);
  
  const [activeTab, setActiveTab] = useState('agent'); 
  const [manualOrigin, setManualOrigin] = useState('DEL');
  const [manualDestination, setManualDestination] = useState('GOI');
  
  // Results & Filters
  const [rawSearchResults, setRawSearchResults] = useState<any[]>([]);
  const [filterPrice, setFilterPrice] = useState('all');
  const [filterSort, setFilterSort] = useState('relevance');
  
  const [selectedItem, setSelectedItem] = useState<any | null>(null);

  // LSTM price prediction state
  const [lstmPredictions, setLstmPredictions] = useState<Record<number, any>>({});
  const [planLstmPrediction, setPlanLstmPrediction] = useState<any | null>(null);
  const [lstmModelInfo, setLstmModelInfo] = useState<any | null>(null);
  const [lstmLoading, setLstmLoading] = useState<Record<number, boolean>>({});

  const [formData, setFormData] = useState({
    origin: 'DEL',
    destination: 'GOI',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0],
    budget: 10000,
    category: 'budget',
    flexibility: true
  });

  useEffect(() => {
    getTrending().then(setTrending).catch(console.error);
    getOffers().then(setOffers).catch(console.error);
  }, []);

  const handleTabChange = (tab: string) => {
      setActiveTab(tab);
      setRawSearchResults([]);
      setFilterSort('relevance');
      setPlan(null);
      if (tab === 'mytrips') fetchMyTrips();
  };

  const fetchMyTrips = async () => {
      setLoading(true);
      try {
          const trips = await getMyTrips();
          setRawSearchResults(trips);
      } catch(e) { console.error(e); }
      setLoading(false);
  }

  const handleManualSearch = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setLstmPredictions({});
      try {
          if (activeTab === 'hotels') {
              const res = await searchHotels(manualDestination);
              setRawSearchResults(res);
          } else if (['flights', 'trains', 'buses'].includes(activeTab)) {
              let type = 'flight';
              if (activeTab === 'trains') type = 'train';
              if (activeTab === 'buses') type = 'bus';
              const res = await searchTransport(manualOrigin, manualDestination, type);
              setRawSearchResults(res);
              // Auto-fetch LSTM predictions for all transport results
              fetchAllLstmPredictions(res, manualOrigin, manualDestination);
          }
      } catch(e) { console.error(e); }
      setLoading(false);
  };

  const handlePlanTrip = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPlanLstmPrediction(null);
    try {
      const input = {
        origin: formData.origin,
        destination: formData.destination,
        start_date: formData.start_date,
        end_date: formData.end_date,
        budget: Number(formData.budget),
        preferences: { category: formData.category, flexibility: formData.flexibility }
      };
      const result = await planTrip(input);
      setPlan(result);
      // Fetch LSTM prediction for the selected transport
      const pred = await predictPrice(formData.origin, formData.destination, result.transport.cost, result.transport.type);
      setPlanLstmPrediction(pred);
      // Fetch model info once
      if (!lstmModelInfo) getLstmModelInfo().then(setLstmModelInfo).catch(console.error);
    } catch (error) { console.error(error); }
    setLoading(false);
  };

  const handleReplan = async () => {
    if (!plan) return;
    setLoading(true);
    try {
      const result = await updatePlan(plan.id, "Simulated price surge on Flights");
      setPlan(result);
      // Re-run LSTM prediction after replanning
      const pred = await predictPrice(result.origin, result.destination, result.transport.cost, result.transport.type);
      setPlanLstmPrediction(pred);
    } catch (error) { console.error(error); }
    setLoading(false);
  };

  const fetchLstmForIndex = async (item: any, idx: number, origin: string, destination: string) => {
    setLstmLoading(prev => ({ ...prev, [idx]: true }));
    try {
      const pred = await predictPrice(origin, destination, item.cost, item.type || 'Flight');
      setLstmPredictions(prev => ({ ...prev, [idx]: pred }));
    } catch (e) { console.error(e); }
    setLstmLoading(prev => ({ ...prev, [idx]: false }));
  };

  const fetchAllLstmPredictions = async (items: any[], origin: string, destination: string) => {
    items.forEach((item, idx) => {
      if (item.cost) fetchLstmForIndex(item, idx, origin, destination);
    });
  };

  const mapMarkers = plan ? [
      { lat: plan.accommodation.coordinates.lat, lng: plan.accommodation.coordinates.lng, popup: plan.accommodation.name },
      ...plan.itinerary.flatMap((d: any) => d.activities.map((act: any) => ({
          lat: act.coordinates.lat, lng: act.coordinates.lng, popup: act.description
      })))
  ] : [];

  // Filter Computation
  const searchResults = rawSearchResults.filter(item => {
      if (filterPrice === 'low' && (item.cost > 5000 || item.cost_per_night > 5000)) return false;
      return true;
  }).sort((a, b) => {
      if (filterSort === 'price_asc') return (a.cost || a.cost_per_night) - (b.cost || b.cost_per_night);
      if (filterSort === 'rating_desc') return (b.rating || 0) - (a.rating || 0);
      return 0;
  });

  const getWeatherIcon = (condition: string) => {
      if (condition.includes("Rain")) return <CloudRain />;
      if (condition.includes("Clear") || condition.includes("Sunny")) return <Sun />;
      return <Cloud />;
  }

  return (
    <div className="bg-app min-h-screen">
      <AnimatePresence>
          {selectedItem && (
            <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="modal-overlay">
                <div className="modal-content">
                    <button className="modal-close" onClick={() => setSelectedItem(null)}><X size={24}/></button>
                    <h2 className="mb-4">
                        {activeTab === 'hotels' || selectedItem.name ? <Hotel className="inline mr-2 text-primary" /> : <MapPin className="inline mr-2 text-accent" />}
                        {activeTab === 'hotels' || selectedItem.name ? selectedItem.name : selectedItem.provider}
                    </h2>
                    
                    <div className="grid layout-2-col gap-6">
                        <div>
                            {activeTab === 'hotels' || selectedItem.name ? (
                                <>
                                    <img src={selectedItem.images[0]} style={{width:'100%', borderRadius:'8px', height:'200px', objectFit:'cover'}} />
                                    <div className="mt-4 mb-2 text-xl font-bold">₹{selectedItem.cost_per_night} / night</div>
                                    <div className="text-muted mb-2">Amenities: {selectedItem.amenities.join(', ')}</div>
                                    <div className="text-yellow-500 font-bold mb-4">{selectedItem.rating} ★ Rating from Foursquare Auth</div>
                                    <button className="large-btn" style={{width:'auto', padding:'10px 24px'}}>Proceed to Reservation</button>
                                </>
                            ) : (
                                <>
                                    <div className="text-xl text-primary font-bold mb-4">₹{selectedItem.cost} Total</div>
                                    <div className="flex justify-between bg-gray-900 p-4 rounded-xl mb-4">
                                        <div><div className="text-muted text-sm">Departure</div><div className="font-bold text-lg">{selectedItem.departure}</div></div>
                                        <div className="text-center font-bold text-accent px-4 pt-1">— {selectedItem.duration} —</div>
                                        <div><div className="text-muted text-sm">Arrival</div><div className="font-bold text-lg">{selectedItem.arrival}</div></div>
                                    </div>

                                    {selectedItem.skyscanner_link && (
                                        <a href={selectedItem.skyscanner_link} target="_blank" rel="noreferrer" className="large-btn inline-flex mb-4" style={{textDecoration:'none', width:'auto'}}>
                                            Track Live  <ExternalLink size={16} className="ml-2" />
                                        </a>
                                    )}
                                </>
                            )}
                        </div>
                        <div className="border border-gray-800 rounded-xl overflow-hidden" style={{height:'300px'}}>
                            {/* OSM / MapBox location rendering */}
                            <div className="bg-gray-900 p-2 text-primary font-bold text-sm border-b border-gray-800"><MapPin size={14} className="inline mb-1 mr-1"/> OSM / MapBox Live Route Map</div>
                            <MapWidget 
                                key={selectedItem.name || selectedItem.provider || manualDestination}
                                center={selectedItem.coordinates || (selectedItem.points && selectedItem.points[1]) || {lat: 28.61, lng: 77.20}} 
                                markers={
                                    (activeTab === 'hotels' || selectedItem.name)
                                      ? [{ lat: selectedItem.coordinates.lat, lng: selectedItem.coordinates.lng, popup: selectedItem.name }]
                                      : selectedItem.points?.map((p: any) => ({lat: p.lat, lng: p.lng, popup: 'Transit Route'})) || []
                                } 
                            />
                        </div>
                    </div>
                </div>
            </motion.div>
          )}
      </AnimatePresence>

      <header className="header flex justify-between items-center p-4">
        <div className="logo flex items-center gap-2 cursor-pointer" onClick={() => handleTabChange('agent')}>
            <Plane size={28} className="text-primary" />
            <h1 className="text-xl m-0 font-bold tracking-tighter">Escape</h1>
        </div>
        <nav className="flex gap-6 hidden-mobile">
            <a href="#" className={`nav-link ${activeTab==='flights'?'active':''}`} onClick={()=>handleTabChange('flights')}><Plane size={18} className="inline mr-1"/> Flights</a>
            <a href="#" className={`nav-link ${activeTab==='hotels'?'active':''}`} onClick={()=>handleTabChange('hotels')}><Hotel size={18} className="inline mr-1"/> Hotels</a>
            <a href="#" className={`nav-link ${activeTab==='trains'?'active':''}`} onClick={()=>handleTabChange('trains')}><Train size={18} className="inline mr-1"/> Trains</a>
            <a href="#" className={`nav-link ${activeTab==='buses'?'active':''}`} onClick={()=>handleTabChange('buses')}><Bus size={18} className="inline mr-1"/> Buses</a>
            <a href="#" className={`nav-link premium-nav ${activeTab==='agent'?'font-bold':''}`} onClick={()=>handleTabChange('agent')}><MapIcon size={18} className="inline mr-1"/> Planner Agents</a>
        </nav>
        <div className="flex gap-4">
            <button className="secondary outline-btn" onClick={() => handleTabChange('mytrips')}><Briefcase size={16}/> My Trips</button>
        </div>
      </header>

      <div className="hero-section">
          <div className="search-container glass-panel animate-fade-in mt-[-40px]">
              <div className="tabs flex gap-4 mb-6 pt-2 overflow-x-auto">
                  <div className={`tab ${activeTab==='flights'?'active':''}`} onClick={()=>handleTabChange('flights')}><Plane size={20}/> Flights</div>
                  <div className={`tab ${activeTab==='hotels'?'active':''}`} onClick={()=>handleTabChange('hotels')}><Hotel size={20}/> Hotels</div>
                  <div className={`tab ${activeTab==='trains'?'active':''}`} onClick={()=>handleTabChange('trains')}><Train size={20}/> Trains</div>
                  <div className={`tab ${activeTab==='buses'?'active':''}`} onClick={()=>handleTabChange('buses')}><Bus size={20}/> Buses</div>
                  <div className={`tab ${activeTab==='agent'?'active font-bold text-accent':''}`} onClick={()=>handleTabChange('agent')}>
                      <MapPin size={20}/> AI Autonomous Planner
                  </div>
              </div>

              {activeTab === 'agent' && (
              <form onSubmit={handlePlanTrip} className="search-form grid gap-4">
                  <div className="form-group">
                    <label>From</label>
                    <input type="text" value={formData.origin} onChange={(e) => setFormData({...formData, origin: e.target.value})} placeholder="e.g. DEL" />
                  </div>
                  <div className="form-group">
                    <label>To</label>
                    <input type="text" value={formData.destination} onChange={(e) => setFormData({...formData, destination: e.target.value})} placeholder="e.g. GOI" />
                  </div>
                  <div className="form-group">
                    <label>Start Date</label>
                    <input type="date" value={formData.start_date} onChange={(e) => setFormData({...formData, start_date: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>End Date</label>
                    <input type="date" value={formData.end_date} onChange={(e) => setFormData({...formData, end_date: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>Travel Style</label>
                    <select value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
                        <option value="budget">Budget</option>
                        <option value="luxury">Luxury</option>
                        <option value="adventure">Adventure</option>
                    </select>
                  </div>
                  <div className="form-group flex justify-center mt-6">
                    <button type="submit" disabled={loading} className="large-btn">
                        {loading ? <RefreshCw className="animate-spin" /> : <Search />}
                        {loading ? 'AI Executing...' : 'Search & Plan'}
                    </button>
                  </div>
              </form>
              )}

              {['flights', 'trains', 'buses'].includes(activeTab) && (
              <form onSubmit={handleManualSearch} className="search-form flex justify-center items-end gap-4 px-4 pb-4">
                  <div className="form-group" style={{width:'300px'}}>
                    <label>Origin</label>
                    <input type="text" value={manualOrigin} onChange={(e) => setManualOrigin(e.target.value)} placeholder="e.g. DEL" />
                  </div>
                  <div className="form-group" style={{width:'300px'}}>
                    <label>Destination</label>
                    <input type="text" value={manualDestination} onChange={(e) => setManualDestination(e.target.value)} placeholder="e.g. GOI" />
                  </div>
                  <div className="form-group mb-0">
                    <button type="submit" disabled={loading} className="large-btn" style={{padding:'12px 32px'}}>
                        {loading ? <RefreshCw className="animate-spin" /> : <Search />}
                        Compare Platforms
                    </button>
                  </div>
              </form>
              )}

              {activeTab === 'hotels' && (
              <form onSubmit={handleManualSearch} className="search-form flex justify-center items-end gap-4 px-4 pb-4">
                  <div className="form-group" style={{width:'400px'}}>
                    <label>Foursquare Destination Search</label>
                    <input type="text" value={manualDestination} onChange={(e) => setManualDestination(e.target.value)} placeholder="e.g. Goa, Delhi..." />
                  </div>
                  <div className="form-group mb-0">
                    <button type="submit" disabled={loading} className="large-btn" style={{padding:'12px 32px'}}>
                        {loading ? <RefreshCw className="animate-spin" /> : <Search />}
                        Fetch Places
                    </button>
                  </div>
              </form>
              )}
          </div>
      </div>

      <div className="container main-content grid gap-8" style={{ gridTemplateColumns: '1fr' }}>
        
        {/* Results with Filter Layer */}
        {['flights', 'hotels', 'trains', 'buses'].includes(activeTab) && rawSearchResults.length > 0 && (
            <div className="dashboard animate-fade-in text-white">
                <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-4">
                    <h2 className="capitalize">Available {activeTab}</h2>
                    <div className="flex gap-4 items-center">
                        <select className="p-2" style={{width:'160px'}} value={filterPrice} onChange={e => setFilterPrice(e.target.value)}>
                            <option value="all">All Prices</option>
                            <option value="low">Under ₹5,000</option>
                        </select>
                        <select className="p-2" style={{width:'150px'}} value={filterSort} onChange={e => setFilterSort(e.target.value)}>
                            <option value="relevance">Top Relevance</option>
                            <option value="price_asc">Price: Low to High</option>
                            {activeTab === 'hotels' && <option value="rating_desc">Top Rated (Foursquare)</option>}
                        </select>
                    </div>
                </div>

                <div className={activeTab === 'hotels' ? "grid grid-cols-3 gap-6" : "flex flex-col gap-4"}>
                    {searchResults.map((item: any, i: number) => (
                        <div key={i} className={`card ${activeTab==='hotels' ? 'hotel-card-vertical' : 'flex justify-between items-center'} text-sm hover:border-primary transition cursor-pointer`} onClick={() => setSelectedItem(item)}>
                            {activeTab === 'hotels' ? (
                                <>
                                    <img src={item.images[0]} />
                                    <div className="hotel-card-vertical-content">
                                        <h4 className="text-xl text-primary font-bold mb-1">{item.name}</h4>
                                        <div className="text-muted mb-3 flex items-center gap-2">{item.type} • <span className="bg-gray-800 px-2 py-1 rounded text-white"><Star size={12} className="inline text-yellow-500 mb-1"/> {item.rating}</span></div>
                                        <div className="text-2xl font-bold mb-2">₹{item.cost_per_night}<span className="text-sm font-normal text-muted">/night</span></div>
                                        <div className="mt-4"><button className="large-btn" style={{padding:'8px 16px', fontSize:'0.9rem'}}>View Details & Map</button></div>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div>
                                        <h4 className="text-lg text-white mb-1 flex items-center gap-2">
                                            {activeTab === 'flights' && <Plane size={18} className="text-primary"/>}
                                            {activeTab === 'trains' && <Train size={18} className="text-accent"/>}
                                            {activeTab === 'buses' && <Bus size={18} className="text-yellow-500"/>}
                                            {item.provider}
                                        </h4>
                                        <div className="text-muted">Dep: {item.departure} — Arr: {item.arrival}</div>
                                    </div>
                                    <div className="text-center text-muted font-bold tracking-widest">{item.duration}</div>
                                    <div className="text-right">
                                        <div className="text-xl font-bold text-accent mb-2">₹{item.cost}</div>
                                        {lstmPredictions[i] ? (
                                            <div className={`text-xs font-bold px-2 py-1 rounded-lg mb-2 flex items-center gap-1 justify-end ${lstmPredictions[i].trend === 'UP' ? 'text-red-400 bg-red-900/30' : 'text-green-400 bg-green-900/30'}`}>
                                                {lstmPredictions[i].trend === 'UP' ? <TrendingUp size={12}/> : <TrendingDown size={12}/>}
                                                {lstmPredictions[i].trend} {lstmPredictions[i].confidence}%
                                            </div>
                                        ) : lstmLoading[i] ? (
                                            <div className="text-xs text-muted mb-2 flex items-center gap-1 justify-end"><Brain size={12} className="animate-pulse"/> Predicting…</div>
                                        ) : null}
                                        <button className="primary rounded bg-white text-black font-bold" style={{padding:'6px 16px'}}>Route Details</button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* My Trips */}
        {activeTab === 'mytrips' && (
            <div className="dashboard animate-fade-in">
                <h2 className="mb-6"><Briefcase className="inline mr-2 text-primary" size={24}/> My Trips</h2>
                {rawSearchResults.length === 0 ? <p className="text-muted">No trips planned yet! Use the Agentic AI planner to build itineraries.</p> : (
                    <div className="grid grid-cols-2 gap-4">
                        {rawSearchResults.map((trip: any, i: number) => (
                            <div key={i} className="card hover:border-primary transition p-6 cursor-pointer" onClick={() => { setPlan(trip); setActiveTab('agent'); }}>
                                <div className="flex justify-between items-center mb-2">
                                    <h3 className="text-xl">{trip.destination}</h3>
                                    <span className={`badge ${trip.budget_adherence ? 'success' : 'danger'}`}>{trip.status}</span>
                                </div>
                                <div className="text-muted text-sm my-2">Est. Cost: <strong className="text-white">₹{trip.total_estimated_cost}</strong></div>
                                <div className="text-sm mt-4 pt-4 border-t border-gray-800 text-primary font-bold">Resume Itinerary →</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        )}

        {/* Agentic Output Dashboard */}
        <AnimatePresence mode="wait">
          {activeTab === 'agent' && plan && (
            <motion.div 
              key="plan"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="dashboard"
            >
              <div className="flex justify-between items-center mb-6">
                <h2>Generated AI Itinerary for {plan.destination}</h2>
                <div className="flex gap-3 items-center">
                  <button onClick={handleReplan} disabled={loading} className="secondary outline-btn flex items-center gap-2">
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''}/> Simulate Fluctuation &amp; Re-optimize
                  </button>
                  <span className={`badge ${plan.budget_adherence ? 'success' : 'danger'} text-lg px-4 py-2`}>
                    {plan.status.toUpperCase().replace('_', ' ')}
                  </span>
                </div>
              </div>

              {plan.alternative_suggestions.length > 0 && (
                <div className="alert-card mb-6 p-4 rounded-xl" style={{background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
                  <h4 className="flex items-center gap-2 text-danger">
                    <AlertTriangle size={20} /> Optimization Agent Feedback
                  </h4>
                  <ul className="pl-8 mt-2 text-sm text-danger-muted">
                    {plan.alternative_suggestions.map((s: string, i: number) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}

              <div className="grid layout-2-col gap-6">
                <div className="column">
                    <div className="summary-cards grid grid-cols-2 gap-4 mb-6">
                        <div className="card">
                        <span className="text-muted block"><DollarSign size={16} className="inline mr-1"/>Est. Cost</span>
                        <div className="text-2xl font-bold mt-1">₹{plan.total_estimated_cost}</div>
                        </div>
                        <div className="card">
                        <span className="text-muted block flex justify-between">
                            <span><MapPin size={16} className="inline mr-1"/>Location</span>
                            {plan.weather_forecast && (
                                <span className="text-white flex items-center gap-1" title={plan.weather_forecast.description}>
                                    {getWeatherIcon(plan.weather_forecast.condition)} {plan.weather_forecast.temp}°C
                                </span>
                            )}
                        </span>
                        <div className="text-2xl font-bold mt-1">{plan.destination}</div>
                        </div>
                    </div>

                    <div className="card mb-6 p-0 overflow-hidden">
                        <div className="p-4 bg-gray-900 border-b border-gray-800"><MapIcon className="inline mr-2 text-primary" size={20}/> <strong className="text-lg">OSM / MapBox Live Matrix</strong></div>
                        <div className="w-full relative z-0"><MapWidget key={plan.id} center={plan.accommodation.coordinates} markers={mapMarkers} /></div>
                    </div>
                </div>

                <div className="column">
                    <div className="card mb-4 details-card border-l-4 border-l-accent cursor-pointer hover:border-gray-500" onClick={() => setSelectedItem(plan.transport)}>
                        <h4><Plane className="inline mr-2 text-accent" size={20}/>Transport Resolved (Amadeus / Kaggle)</h4>
                        <div className="flex justify-between mt-2">
                            <div>
                                <span className="font-bold block text-lg">{plan.transport.provider}</span>
                                <span className="text-muted">Departs: {plan.transport.departure} • Arr: {plan.transport.arrival} <br/> Duration: {plan.transport.duration}</span>
                            </div>
                            <div className="text-right text-xl font-bold">₹{plan.transport.cost}</div>
                        </div>
                        {planLstmPrediction && (
                            <div className={`mt-3 p-3 rounded-xl flex items-center justify-between text-sm font-bold ${planLstmPrediction.trend === 'UP' ? 'bg-red-900/30 border border-red-500/30' : 'bg-green-900/30 border border-green-500/30'}`}>
                                <div className="flex items-center gap-2">
                                    <Brain size={16} className="text-primary"/>
                                    <span className="text-muted font-normal">LSTM Price Forecast</span>
                                    {planLstmPrediction.trend === 'UP'
                                        ? <TrendingUp size={16} className="text-red-400"/>
                                        : <TrendingDown size={16} className="text-green-400"/>}
                                    <span className={planLstmPrediction.trend === 'UP' ? 'text-red-400' : 'text-green-400'}>
                                        {planLstmPrediction.trend} · {planLstmPrediction.confidence}% confidence
                                    </span>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-muted">Predicted: ₹{planLstmPrediction.predicted_price}</div>
                                    <div className={`text-xs mt-0.5 ${planLstmPrediction.trend === 'UP' ? 'text-red-400' : 'text-green-400'}`}>{planLstmPrediction.recommendation}</div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="card mb-6 details-card border-l-4 border-l-primary cursor-pointer hover:border-gray-500" onClick={() => setSelectedItem(plan.accommodation)}>
                        <h4><Hotel className="inline mr-2 text-primary" size={20}/>Accommodation (Foursquare Auth)</h4>
                        <div className="flex justify-between mt-2 mb-2">
                            <div>
                                <span className="font-bold block text-lg">{plan.accommodation.name}</span>
                                <div className="text-sm my-1"><Star size={14} className="inline text-yellow-500 mr-1"/> {plan.accommodation.rating}/5 Ratings</div>
                            </div>
                            <span className="font-bold text-xl">₹{plan.accommodation.cost_per_night}/nt</span>
                        </div>
                        <img src={plan.accommodation.images[0]} style={{width:'100%', height:'140px', objectFit:'cover', borderRadius:'8px'}} alt="Hotel" />
                        <div className="mt-2 text-sm text-muted">Amenities: {plan.accommodation.amenities.join(', ')}</div>
                    </div>
                </div>
              </div>

              <h3 className="mt-8 mb-4 border-b border-gray-800 pb-2">Optimized Day-wise Flow</h3>
              <div className="grid layout-day-cards gap-4">
                {plan.itinerary.map((day: any) => (
                  <div key={day.day} className="card p-5 itinerary-card relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-primary/50 group-hover:bg-primary transition"></div>
                    <div className="flex justify-between border-b border-gray-800 pb-3 mb-4">
                      <strong className="text-lg">Day {day.day} <span className="text-muted text-sm ml-2">({day.date})</span></strong>
                      <span className="badge font-bold">₹{day.daily_cost}</span>
                    </div>
                    {day.activities.map((act: any, i: number) => (
                      <div key={i} className="flex gap-4 text-sm mt-4 items-start bg-gray-900/50 p-3 rounded hover:bg-gray-800 transition">
                        <div className="text-accent w-20 flex-shrink-0 font-bold tracking-wider"><Clock size={14} className="inline mr-1 mb-1"/>{act.time}</div>
                        <div>
                          <div className="text-md font-semibold text-gray-200">{act.description}</div>
                          <div className="text-xs text-muted flex items-center mt-1"><MapPin size={12} className="inline mr-1 text-gray-500"/> {act.location}</div>
                          <div className="text-xs text-primary mt-1 font-bold">₹{act.cost}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>

            </motion.div>
          )}
        </AnimatePresence>

        {activeTab === 'agent' && !plan && offers.length > 0 && (
            <div className="animate-fade-in mt-4">
                <div className="flex justify-between items-center mb-4 border-b" style={{borderColor:'rgba(124,58,237,0.2)', paddingBottom:'12px'}}>
                    <h2>Special Offers</h2>
                </div>
                <div className="grid gap-4" style={{gridTemplateColumns:'repeat(2,1fr)'}}>
                    {offers.map((o: any) => (
                        <div key={o.id} className="card flex gap-4 items-center p-4">
                            <img src={o.image} alt={o.title} style={{width:'80px', height:'60px', objectFit:'cover', borderRadius:'8px', flexShrink:0}} />
                            <div>
                                <div className="font-bold text-white">{o.title}</div>
                                <div className="text-accent font-bold mt-1">{o.discount}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {activeTab === 'agent' && !plan && trending.length > 0 && (
            <div className="discovery-section animate-fade-in delay-200 mt-4">
                <div className="flex justify-between items-center mb-6 border-b" style={{borderColor:'rgba(124,58,237,0.2)', paddingBottom:'12px'}}>
                    <h2>Trending Destinations</h2>
                    <span className="text-muted text-sm">Click any card to instantly plan your trip ✨</span>
                </div>
                <div className="grid gap-5" style={{gridTemplateColumns:'repeat(3,1fr)'}}>
                    {trending.map((t: any) => (
                        <div
                            key={t.id}
                            className="dest-card relative group cursor-pointer overflow-hidden rounded-2xl"
                            style={{height:'220px', border:'1px solid rgba(124,58,237,0.15)', transition:'all 0.3s'}}
                            onClick={() => {
                                setFormData(prev => ({...prev, destination: t.name}));
                                // Scroll up to form
                                window.scrollTo({top: 0, behavior: 'smooth'});
                            }}
                            onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-6px)', e.currentTarget.style.boxShadow = '0 20px 40px rgba(124,58,237,0.3)')}
                            onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)', e.currentTarget.style.boxShadow = 'none')}
                        >
                            <img
                                src={t.image}
                                alt={t.name}
                                style={{width:'100%', height:'100%', objectFit:'cover', display:'block', transition:'transform 0.5s'}}
                                className="group-hover:scale-110"
                                onError={(e) => { (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=600&auto=format&fit=crop'; }}
                            />
                            {/* Gradient overlay */}
                            <div style={{position:'absolute', inset:0, background:'linear-gradient(to top, rgba(14,11,30,0.95) 0%, rgba(14,11,30,0.3) 60%, transparent 100%)'}}></div>
                            {/* Hover CTA */}
                            <div style={{position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)', opacity:0, transition:'opacity 0.3s'}} className="group-hover:opacity-100">
                                <div style={{background:'linear-gradient(135deg,#7c3aed,#9333ea)', borderRadius:'30px', padding:'10px 24px', color:'white', fontWeight:700, fontSize:'0.9rem', textAlign:'center', whiteSpace:'nowrap', boxShadow:'0 8px 24px rgba(124,58,237,0.5)'}}>
                                    ✈ Plan Trip to {t.name}
                                </div>
                            </div>
                            {/* Bottom info */}
                            <div style={{position:'absolute', bottom:0, left:0, right:0, padding:'16px'}}>
                                <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-end'}}>
                                    <div>
                                        <h3 style={{fontSize:'1.3rem', fontWeight:800, color:'white', marginBottom:'4px'}}>{t.name}</h3>
                                        <p style={{color:'rgba(237,233,254,0.8)', fontSize:'0.85rem'}}>{t.snippet}</p>
                                    </div>
                                    <span style={{background:'rgba(245,158,11,0.2)', border:'1px solid rgba(245,158,11,0.4)', borderRadius:'20px', padding:'4px 10px', fontSize:'0.8rem', fontWeight:700, color:'#f59e0b', whiteSpace:'nowrap'}}>
                                        ★ {t.rating}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}
      </div>
    </div>
  );
}

export default App;
