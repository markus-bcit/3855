import React, { useEffect, useState } from "react";
import "../App.css";

export default function AppStats() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  const getStats = () => {
    fetch(`http://markus-kafka.canadacentral.cloudapp.azure.com/event_logger/event_stats`)
      .then((res) => res.json())
      .then(
        (result) => {
          console.log("Received Stats");
          setStats(result);
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  };
  useEffect(() => {
    const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, [getStats]);

  if (error) {
    return <div className={"error"}>Error found when fetching from API</div>;
  } else if (isLoaded === false) {
    return <div>Loading...</div>;
  } else if (isLoaded === true) {
    return (
      <div>
        <h1>Event Logs</h1>
        <table className={"StatsTable"}>
          <tbody>
            <tr>
              <td>0001 Events Logged: {stats["0001"]}</td>
            </tr>
            <tr>
              <td colspan="2">0002 Events Logged: {stats["0002"]}</td>
            </tr>
            <tr>
              <td colspan="2">
              0003 Events Logged: {stats["0003"]}
              </td>
            </tr>
            <tr>
              <td colspan="2">0004 Events Logged: {stats["0004"]}</td>
            </tr>
          </tbody>
        </table>
        <h3>Last Updated: {stats["last_update"]}</h3>
      </div>
    );
  }
}
