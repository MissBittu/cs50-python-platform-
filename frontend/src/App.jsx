import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { Play, Code, BookOpen, Trophy, Home, LogIn, LogOut, User, CheckCircle, Award, Target, Zap, ChevronRight, Star } from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:8000/api';

// Markdown-like renderer (simple version)
function renderMarkdown(text) {
  return text
    .split('\n')
    .map((line, i) => {
      // Headers
      if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>;
      if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>;
      if (line.startsWith('# ')) return <h1 key={i}>{line.slice(2)}</h1>;
      
      // Code blocks
      if (line.startsWith('```')) return null;
      if (line.trim() === '') return <br key={i} />;
      
      // List items
      if (line.startsWith('- ')) return <li key={i}>{line.slice(2)}</li>;
      
      // Regular text
      return <p key={i}>{line}</p>;
    });
}

function Navbar({ user, onLogout }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <BookOpen size={28} />
        <span>Python Learning Hub</span>
      </div>
      <div className="nav-links">
        <Link to="/" className="nav-link">
          <Home size={18} />
          Home
        </Link>
        <Link to="/courses" className="nav-link">
          <BookOpen size={18} />
          Courses
        </Link>
        {user && (
          <Link to="/dashboard" className="nav-link">
            <Trophy size={18} />
            Dashboard
          </Link>
        )}
      </div>
      <div className="nav-auth">
        {user ? (
          <>
            <div className="points-badge">
              <Star size={16} />
              <span>{user.total_points} pts</span>
            </div>
            <span className="user-name">
              <User size={16} />
              {user.username}
            </span>
            <button onClick={onLogout} className="btn btn-secondary btn-sm">
              <LogOut size={16} />
            </button>
          </>
        ) : (
          <Link to="/login" className="btn btn-primary">
            <LogIn size={16} />
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}

function HomePage() {
  return (
    <div className="home-page">
      <div className="hero">
        <div className="hero-badge">
          <Award size={20} />
          <span>Interactive Python Learning</span>
        </div>
        <h1>Master Python Programming</h1>
        <p className="hero-subtitle">
          Learn Python from basics to advanced with interactive lessons, quizzes, and earn points as you progress!
        </p>
        <div className="hero-buttons">
          <Link to="/courses" className="btn btn-primary btn-lg">
            <Play size={20} />
            Start Learning
          </Link>
          <Link to="/login" className="btn btn-secondary btn-lg">
            <User size={20} />
            Create Account
          </Link>
        </div>
        <div className="hero-stats">
          <div className="stat-item">
            <div className="stat-number">5+</div>
            <div className="stat-label">Python Courses</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">50+</div>
            <div className="stat-label">Interactive Lessons</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">∞</div>
            <div className="stat-label">Practice Quizzes</div>
          </div>
        </div>
      </div>

      <div className="features-section">
        <h2>How It Works</h2>
        <div className="features">
          <div className="feature-card">
            <div className="feature-icon">📚</div>
            <h3>1. Choose Your Level</h3>
            <p>Start with beginner courses or jump to advanced topics based on your skill level.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📖</div>
            <h3>2. Read & Learn</h3>
            <p>Study interactive articles with code examples and video tutorials.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">✅</div>
            <h3>3. Take Quizzes</h3>
            <p>Test your knowledge with quizzes after each lesson and earn points!</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🏆</div>
            <h3>4. Track Progress</h3>
            <p>Monitor your learning journey and celebrate your achievements.</p>
          </div>
        </div>
      </div>

      <div className="cta-section">
        <h2>Ready to Start Your Python Journey?</h2>
        <p>Create a free account and start learning today!</p>
        <Link to="/courses" className="btn btn-primary btn-lg">
          <Play size={20} />
          Explore Courses
        </Link>
      </div>
    </div>
  );
}

function CoursesPage({ user }) {
  const [courses, setCourses] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState('all');
  
  useEffect(() => {
    const level = selectedLevel === 'all' ? undefined : selectedLevel;
    axios.get(`${API_URL}/courses`, { params: { level } })
      .then(res => setCourses(res.data))
      .catch(err => console.error(err));
  }, [selectedLevel]);

  const levels = [
    { value: 'all', label: 'All Levels', icon: '📚' },
    { value: 'beginner', label: 'Beginner', icon: '🌱' },
    { value: 'intermediate', label: 'Intermediate', icon: '🚀' },
    { value: 'advanced', label: 'Advanced', icon: '⚡' }
  ];

  return (
    <div className="courses-page">
      <div className="page-header">
        <h1>Python Courses</h1>
        <p>Choose your learning path</p>
      </div>

      <div className="level-filters">
        {levels.map(level => (
          <button
            key={level.value}
            className={`level-btn ${selectedLevel === level.value ? 'active' : ''}`}
            onClick={() => setSelectedLevel(level.value)}
          >
            <span className="level-icon">{level.icon}</span>
            {level.label}
          </button>
        ))}
      </div>

      <div className="courses-grid">
        {courses.map(course => (
          <Link to={`/courses/${course.id}`} key={course.id} className="course-card">
            <div className="course-icon">{course.icon}</div>
            <div className="course-content">
              <div className="course-level">{course.level}</div>
              <h3>{course.title}</h3>
              <p>{course.description}</p>
            </div>
            <div className="course-arrow">
              <ChevronRight size={20} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function CourseDetailPage({ user }) {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [progress, setProgress] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL}/courses/${courseId}`)
      .then(res => setCourse(res.data))
      .catch(err => console.error(err));

    if (user) {
      axios.get(`${API_URL}/progress/${user.id}`)
        .then(res => setProgress(res.data))
        .catch(err => console.error(err));
    }
  }, [courseId, user]);

  const isCompleted = (articleId) => {
    return progress.some(p => p.article_id === articleId && p.completed);
  };

  if (!course) return <div className="loading">Loading...</div>;

  return (
    <div className="course-detail">
      <div className="course-header">
        <div className="course-icon-large">{course.icon}</div>
        <div>
          <div className="course-level-badge">{course.level}</div>
          <h1>{course.title}</h1>
          <p>{course.description}</p>
        </div>
      </div>

      <div className="articles-list">
        <h2>Lessons</h2>
        {course.articles && course.articles.map((article, index) => (
          <Link 
            to={`/articles/${article.id}`} 
            key={article.id}
            className={`article-item ${isCompleted(article.id) ? 'completed' : ''}`}
          >
            <div className="article-number">{index + 1}</div>
            <div className="article-info">
              <h3>{article.title}</h3>
              {isCompleted(article.id) && (
                <span className="completed-badge">
                  <CheckCircle size={16} /> Completed
                </span>
              )}
            </div>
            <ChevronRight size={20} />
          </Link>
        ))}
      </div>
    </div>
  );
}

function ArticlePage({ user }) {
  const { articleId } = useParams();
  const [article, setArticle] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizResults, setQuizResults] = useState({});
  const [totalScore, setTotalScore] = useState(0);

  useEffect(() => {
    axios.get(`${API_URL}/articles/${articleId}`)
      .then(res => {
        setArticle(res.data);
        setShowQuiz(false);
        setQuizResults({});
        setTotalScore(0);
      })
      .catch(err => console.error(err));
  }, [articleId]);

  const handleQuizSubmit = async (quizId, answer) => {
    if (!user) {
      alert('Please login to take quizzes!');
      return;
    }

    try {
      const res = await axios.post(`${API_URL}/quiz/submit`, 
        { quiz_id: quizId, answer },
        { params: { user_id: user.id } }
      );

      setQuizResults(prev => ({
        ...prev,
        [quizId]: res.data
      }));

      if (res.data.correct) {
        setTotalScore(prev => prev + res.data.points_earned);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const markAsComplete = async () => {
    if (!user) {
      alert('Please login to save progress!');
      return;
    }

    try {
      await axios.post(`${API_URL}/progress`, 
        { article_id: parseInt(articleId), completed: true, score: totalScore },
        { params: { user_id: user.id } }
      );
      alert(`✅ Lesson completed! You earned ${totalScore} points!`);
    } catch (err) {
      console.error(err);
    }
  };

  if (!article) return <div className="loading">Loading...</div>;

  return (
    <div className="article-page">
      <div className="article-content">
        <h1>{article.title}</h1>
        
        {article.video_url && (
          <div className="video-container">
            <iframe
              width="100%"
              height="400"
              src={article.video_url}
              title={article.title}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
        )}

        <div className="article-body">
          {renderMarkdown(article.content)}
        </div>

        {!showQuiz && article.quizzes && article.quizzes.length > 0 && (
          <button 
            onClick={() => setShowQuiz(true)} 
            className="btn btn-primary btn-lg"
          >
            <Target size={20} />
            Take Quiz ({article.quizzes.length} questions)
          </button>
        )}

        {showQuiz && (
          <div className="quiz-section">
            <h2>📝 Quiz Time!</h2>
            {article.quizzes.map((quiz, index) => (
              <QuizQuestion
                key={quiz.id}
                quiz={quiz}
                index={index}
                result={quizResults[quiz.id]}
                onSubmit={handleQuizSubmit}
              />
            ))}

            {Object.keys(quizResults).length === article.quizzes.length && (
              <div className="quiz-complete">
                <h3>🎉 Quiz Complete!</h3>
                <p>Total Score: {totalScore} points</p>
                <button onClick={markAsComplete} className="btn btn-primary">
                  <CheckCircle size={20} />
                  Complete Lesson
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function QuizQuestion({ quiz, index, result, onSubmit }) {
  const [selectedAnswer, setSelectedAnswer] = useState('');

  const handleSubmit = () => {
    if (selectedAnswer) {
      onSubmit(quiz.id, selectedAnswer);
    }
  };

  const options = [
    { value: 'A', text: quiz.option_a },
    { value: 'B', text: quiz.option_b },
    { value: 'C', text: quiz.option_c },
    { value: 'D', text: quiz.option_d }
  ];

  return (
    <div className={`quiz-question ${result ? 'answered' : ''}`}>
      <h4>Question {index + 1}</h4>
      <p>{quiz.question}</p>

      <div className="quiz-options">
        {options.map(option => (
          <label 
            key={option.value}
            className={`quiz-option ${
              result && result.correct && selectedAnswer === option.value ? 'correct' :
              result && !result.correct && selectedAnswer === option.value ? 'incorrect' :
              ''
            }`}
          >
            <input
              type="radio"
              name={`quiz-${quiz.id}`}
              value={option.value}
              checked={selectedAnswer === option.value}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              disabled={!!result}
            />
            <span>{option.value}. {option.text}</span>
          </label>
        ))}
      </div>

      {!result && (
        <button 
          onClick={handleSubmit} 
          className="btn btn-primary btn-sm"
          disabled={!selectedAnswer}
        >
          Submit Answer
        </button>
      )}

      {result && (
        <div className={`quiz-result ${result.correct ? 'correct' : 'incorrect'}`}>
          {result.correct ? (
            <>✅ Correct! +{result.points_earned} points</>
          ) : (
            <>❌ Incorrect. Correct answer: {result.correct_answer}</>
          )}
        </div>
      )}
    </div>
  );
}

function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isRegister) {
        await axios.post(`${API_URL}/register`, { username, email, password });
        alert('✅ Registration successful! Please login.');
        setIsRegister(false);
        setPassword('');
      } else {
        const res = await axios.post(`${API_URL}/login`, { username, password });
        onLogin(res.data.user);
        navigate('/courses');
      }
    } catch (error) {
      alert('❌ ' + (error.response?.data?.detail || 'An error occurred'));
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <BookOpen size={40} />
          <h2>{isRegister ? 'Create Account' : 'Welcome Back'}</h2>
          <p>{isRegister ? 'Start your Python learning journey' : 'Continue learning Python'}</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          {isRegister && (
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          )}
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary btn-block">
            {isRegister ? 'Create Account' : 'Login'}
          </button>
        </form>
        <p className="toggle-auth">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}
          <button onClick={() => setIsRegister(!isRegister)} className="link-btn">
            {isRegister ? 'Login' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  );
}

function DashboardPage({ user }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (user) {
      axios.get(`${API_URL}/stats/${user.id}`)
        .then(res => setStats(res.data))
        .catch(err => console.error(err));
    }
  }, [user]);

  if (!user) {
    return (
      <div className="dashboard-empty">
        <Trophy size={60} />
        <h2>Please Login</h2>
        <p>Login to view your progress and achievements</p>
        <Link to="/login" className="btn btn-primary">Login Now</Link>
      </div>
    );
  }

  if (!stats) return <div className="loading">Loading...</div>;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1>Welcome back, {stats.username}! 👋</h1>
          <p>Here's your learning progress</p>
        </div>
        <div className="total-points">
          <Star size={30} />
          <div>
            <div className="points-value">{stats.total_points}</div>
            <div className="points-label">Total Points</div>
          </div>
        </div>
      </div>

      <div className="progress-overview">
        <h3>Overall Progress</h3>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${stats.completion_rate}%` }}></div>
        </div>
        <p>{stats.completion_rate}% Complete ({stats.completed_articles}/{stats.total_articles} lessons)</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card primary">
          <div className="stat-icon"><CheckCircle size={30} /></div>
          <div className="stat-content">
            <div className="stat-value">{stats.completed_articles}</div>
            <div className="stat-label">Lessons Completed</div>
          </div>
        </div>
        <div className="stat-card success">
          <div className="stat-icon"><Target size={30} /></div>
          <div className="stat-content">
            <div className="stat-value">{stats.total_articles}</div>
            <div className="stat-label">Total Lessons</div>
          </div>
        </div>
        <div className="stat-card warning">
          <div className="stat-icon"><Trophy size={30} /></div>
          <div className="stat-content">
            <div className="stat-value">{stats.completion_rate}%</div>
            <div className="stat-label">Completion Rate</div>
          </div>
        </div>
      </div>

      {stats.recent_activities && stats.recent_activities.length > 0 && (
        <div className="recent-activity">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            {stats.recent_activities.map((activity, index) => (
              <div key={index} className="activity-item">
                <CheckCircle size={20} className="activity-icon" />
                <div className="activity-info">
                  <div className="activity-title">{activity.title}</div>
                  <div className="activity-meta">
                    {activity.score} points · {new Date(activity.completed_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="next-steps">
        <h3>Continue Learning</h3>
        <Link to="/courses" className="action-card">
          <BookOpen size={30} />
          <h4>Explore Courses</h4>
          <p>Find your next lesson</p>
        </Link>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <Router>
      <div className="app">
        <Navbar user={user} onLogout={handleLogout} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/courses" element={<CoursesPage user={user} />} />
            <Route path="/courses/:courseId" element={<CourseDetailPage user={user} />} />
            <Route path="/articles/:articleId" element={<ArticlePage user={user} />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/dashboard" element={<DashboardPage user={user} />} />
          </Routes>
        </main>
        <footer className="footer">
          <p>© 2025 Python Learning Hub | Built for learners, by learners ❤️</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;