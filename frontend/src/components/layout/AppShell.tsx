import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import ApprovalCard from "@/components/approval/ApprovalCard";

export default function AppShell(): JSX.Element {
  return (
    <div className="min-h-screen bg-bg-base text-text-primary">
      <Sidebar />
      <Topbar />
      <main className="min-h-screen pl-60 pt-12">
        <div className="min-h-[calc(100vh-3rem)] px-4 py-4">
          <Outlet />
        </div>
      </main>
      <ApprovalCard />
    </div>
  );
}

