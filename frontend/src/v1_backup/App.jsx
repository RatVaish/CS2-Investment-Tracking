import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TabLayout from './components/TabLayout.jsx';
import Home from './pages/Home.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Manage from './pages/Manage.jsx';
import Portfolio from './pages/Portfolio.jsx';

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
