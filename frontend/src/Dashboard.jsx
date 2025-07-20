import { useEffect, useState } from 'react';
import { api } from './api';

export default function Dashboard({ user }) {
  const [semesters, setSemesters] = useState([]);
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const semRes = await api('/semesters');
        setSemesters(semRes.data);
      } catch (e) {
        console.error(e);
      }
    }
    fetchData();
  }, []);

  const loadCourses = async (semesterId) => {
    try {
      const res = await api(`/semesters/${semesterId}/courses`);
      setCourses(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div>
      <h2>欢迎, {user.username}</h2>
      <h3>学期列表</h3>
      <ul>
        {semesters.map(s => (
          <li key={s.id}>
            <button onClick={() => loadCourses(s.id)}>{s.name}</button>
          </li>
        ))}
      </ul>
      {courses.length > 0 && (
        <div>
          <h3>课程列表</h3>
          <ul>
            {courses.map(c => <li key={c.id}>{c.name}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
