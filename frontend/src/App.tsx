import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';
import { ChatPage } from './pages/ChatPage';
import { UploadPage } from './pages/UploadPage';

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-background overflow-hidden font-sans text-text">
        <Sidebar />
        <div className="flex-1 flex flex-col lg:ml-64 relative w-full overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-y-auto relative h-full">
            <Routes>
              <Route path="/" element={<ChatPage />} />
              <Route path="/upload" element={<UploadPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
