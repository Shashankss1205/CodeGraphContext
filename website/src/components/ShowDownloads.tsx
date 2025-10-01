import { useEffect, useState } from "react";

type PypiStats = {
  data: {
    last_day: number;
    last_month: number;
    last_week: number;
  };
  package: string;
  type: string;
};

export default function ShowDownloads() {
  const [stats, setStats] = useState<PypiStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch("/api/pypi/packages/codegraphcontext/recent");

        if (!res.ok) {
          throw new Error(`API error: ${res.status}`);
        }

        const data = await res.json();
        setStats(data);
      } catch (err: unknown) {
        setError((err as Error).message);
      }
    }
    fetchStats();
  }, []);

  if (error) return <p className="text-red-500">Error: {error}</p>;
  if (!stats) return <p>Loading stats...</p>;

  return (
    <>
      {stats?.data ? (
        <>
          <p>Last month downloads: {stats.data.last_month.toLocaleString()}+</p>
        </>
      ) : (
        <p>No data available yet for this package</p>
      )}
    </>
  );
}