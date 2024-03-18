import React, { useEffect, useState } from "react";
import "../App.css";

export default function AppStats() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  const getStats = () => {
    fetch(`http://markus-kafka.canadacentral.cloudapp.azure.com:8100/stats`)
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
        <h1>Latest Stats</h1>
        <table className={"StatsTable"}>
          <tbody>
            <tr>
              <th>Workout</th>
              <th>Workout Log</th>
            </tr>
            <tr>
              <td># Workout: {stats["num_workouts"]}</td>
              <td># Workout Logs: {stats["num_workout_logs"]}</td>
            </tr>
            <tr>
              <td colspan="2">Max Workout Freq: {stats["max_freq_workout"]}</td>
            </tr>
            <tr>
              <td colspan="2">
                Min Workout Freq: {stats["min_freq_workout"]}
              </td>
            </tr>
            <tr>
              <td colspan="2">Max Freq Workout: {stats["max_freq_workout"]}</td>
            </tr>
          </tbody>
        </table>
        <h3>Last Updated: {stats["last_update"]}</h3>
      </div>
    );
  }
}
