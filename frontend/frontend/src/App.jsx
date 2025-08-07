import { BrowserRouter, Routes, Route } from "react-router-dom";
import RagAssistantUI from "./components/RagAssistantUI";

function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RagAssistantUI />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
