import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          O.M.E.G.A Framework
        </h1>
        <p className="text-xl mb-10">
          Orchestrated Multi-Expert Gen Agents
        </p>
        <Link 
          href="/dashboard" 
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
        >
          Enter Dashboard
        </Link>
      </div>
    </main>
  );
}
