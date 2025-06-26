import { IUser } from '../interfaces/IUSer';

interface WelcomeProps {
  user: IUser | undefined;
  setCurrentLayer: (layer: string) => void;
}

const Welcome: React.FC<WelcomeProps> = ({ user, setCurrentLayer }) => {
  const seeAllTasks = () => {
    // Navigate to a dedicated tasks page or show a modal
    console.log('See all tasks');
    // Example: setCurrentLayer('TASKS');
  };

  const toggleTask = (taskId: string) => {
    console.log(`Toggle task ${taskId}`);
    // Here you would handle the task completion logic
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-blue-50 to-indigo-50 text-black">
      {/* Header */}
      <div className="pt-12 px-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Schedy</h1>
            <p className="text-xs opacity-50 mt-1">AI Schedule Assistant</p>
          </div>
          <button
            onClick={() => setCurrentLayer('PROFILE')}
            className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center hover:bg-indigo-200 transition-all duration-300 hover:scale-110"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 px-6 pt-8 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Welcome back, {user?.name}!</h2>
          <p className="opacity-70">Ready to organize your day with voice commands?</p>
        </div>

        {/* Today's Tasks */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Today's Tasks</h2>
            <button onClick={seeAllTasks} className="text-sm text-indigo-600 hover:text-indigo-800 transition-colors font-medium">
              See all
            </button>
          </div>

          <div className="space-y-3">
            {/* Example Task Card */}
            <button onClick={() => toggleTask('morning-workout')} className="task-card w-full bg-white rounded-xl p-4 shadow-sm text-left border border-gray-100">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">Morning Workout</h3>
                  <p className="text-xs opacity-60">7:00 AM - 8:00 AM</p>
                  <p className="text-xs text-gray-500 mt-1">🎤 "Напомни мне сделать утреннюю зарядку в 7 утра"</p>
                </div>
                <div className="flex flex-col items-end">
                  <div className="bg-red-100 px-3 py-1 rounded-full mb-2">
                    <span className="text-xs text-red-700 font-medium">High</span>
                  </div>
                  <div className="w-5 h-5 border-2 border-gray-300 rounded"></div>
                </div>
              </div>
            </button>
            {/* Add other tasks similarly */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
