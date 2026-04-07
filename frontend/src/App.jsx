import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TabLayout from './components/TabLayout';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Manage from './pages/Manage';
import Portfolio from './pages/Portfolio';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import Cookies from './pages/Cookies';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Main app with navbar/tab layout */}
        <Route path="/" element={<TabLayout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="manage" element={<Manage />} />
          <Route path="portfolio" element={<Portfolio />} />
        </Route>

        {/* Legal pages — standalone, no TabLayout */}
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/cookies" element={<Cookies />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
