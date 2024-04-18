import React, { useEffect, useState } from "react";
import "../App.css";

export default function AppStats() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  const getStats = () => {
    fetch(`http://markus-kafka.canadacentral.cloudapp.azure.com/anomaly_detector/anomaly_stats`)
      .then((res) => res.json())
      .then(
        (result) => {
          console.log("Received anomaly");
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
        <h1>Anomalies</h1>
        <table className={"StatsTable"}>
          <tbody>
            <tr>
              <td><h3>Workout Anomalies</h3> {stats["workout_log"]}</td>
            </tr>
            <tr>
              <td colspan="2"><h3>Workout Log Anomalies</h3> {stats["workout"]}</td>
            </tr>
            <tr>
              <td colspan="2">
              Total # of anomalies {stats["num_anomalies"]}
              </td>
            </tr>
            <tr>
              <td colspan="2"><h3>Description:</h3> {stats["most_recent_desc"]}</td>
            </tr>
            <tr>
              <td colspan="2"><h3>Last Updated:</h3> {stats["most_recent_datetime"]}</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }
}
