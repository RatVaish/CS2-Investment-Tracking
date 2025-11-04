import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TabLayout from './components/TabLayout';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Manage from './pages/Manage';
import Portfolio from './pages/Portfolio';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TabLayout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="manage" element={<Manage />} />
          <Route path="portfolio" element={<Portfolio />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
