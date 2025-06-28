import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import "../../../styles/Questions.css";

export default function Marks() {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters,setFilters] = useState({
    status:"",
    type:"",
    start_time :"",
  });
  
  const navigate = useNavigate();

  useEffect(() => {
    const loadTests = async () => {
      try {
        const res = await axiosInstance.get("/marks/");
        setTests(res.data);
      } catch (err) {
        console.error("Failed to load tests:", err);
      } finally {
        setLoading(false);
      }
    };
    loadTests();
  }, []);

    const fetchTests = async () =>{
    try {
      const params = {};
      if(searchTerm) params.search = searchTerm;
      if(filters.status) params.status = filters.status;
      if(filters.type) params.type = filters.type;
      if(filters.start_time) params.start_time__date = filters.start_time;
      console.log(filters.start_time)
      console.log(params.start_time__date)

      const res = await axiosInstance.get("/marks/", {params});
      console.log("Marks tests with filters:", res.data);
      setTests(res.data);
    } catch (err){
      console.error("Failed to load marks:", err);
    }
  };

  const handleSearchChange = (e) => setSearchTerm(e.target.value);

  const handleFilterChange = (e) => {
    const {name, value} = e.target;
    setFilters({...filters, [name]:value});
  };

  const handleResetFilters = () => {
    setSearchTerm("");
    setFilters({status:"", type:"", start_time:""});
    fetchTests();
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTests();
  }
  
  if (loading) return <p>Loading test summaries...</p>;

  return (
    <div className="questions-page">
      <h2>Marks – Your Tests</h2>

    <form onSubmit={handleSearchSubmit} className="search-filters-container">
            <input
              type = "text"
              placeholder="Search marks..."
              value={searchTerm}
              onChange={handleSearchChange}
            />
            <select
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
            >
              <option value="">All Statuses</option>
              <option value="finalized">Finalized</option>
              <option value="in progress">In Progress</option>
            </select>
            <select name="type" value={filters.type} onChange={handleFilterChange}>
              <option value="">All Types</option>
              <option value="exam">Exam Test</option>
              <option value="seminar">Seminar Test</option>
              <option value="training">Training Test</option>
            </select>
            <input
              type="date"
              name = "start_time"
              value = {filters.start_time}
              onChange={handleFilterChange}
            />
            <button type="submit">Apply Filters</button>
            <button type="button" onClick={handleResetFilters}>Reset Filters</button>
        </form>


      <div className="questions-table-container">
      <table className="questions-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Type</th>
            <th>Start</th>
            <th>Deadline</th>
            <th>Assigned</th>
            <th>Finalized</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tests.map((test, index) => (
            <tr key={test.id}>
              <td>{index + 1}</td>
              <td>{test.name}</td>
              <td>{test.type}</td>
              <td>{test.start_time?.slice(0, 16).replace("T", " ") || "-"}</td>
              <td>{test.deadline?.slice(0, 16).replace("T", " ") || "-"}</td>
              <td>{test.total_assignments}</td>
              <td>{test.finalized_count}</td>
              <td>
                <button onClick={() => navigate(`/marks/${test.id}`)}>
                  View Assignments
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
            </div>
    </div>
  );
}
