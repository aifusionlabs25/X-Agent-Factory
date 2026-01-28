// Helper Component for Task Card (insert in page.tsx or separate file, but for simplicity we keep it in page logic or defined at top)
// Since I can't multi-file refactor easily, I'll define it separate to be appended or inserted?
// No, I need to define it within the replace block or append it. 
// I'll append it to the end of the file or just inline it in the map for now? 
// The map logic was replaced with <TaskCard /> but I didn't define TaskCard. 
// I must define TaskCard.

// I will insert it before the default export.
import React from 'react';

const TaskCard = ({ task, markTaskDone, isOverdue }: any) => (
    <div className={`flex items-start gap-4 p-4 border rounded-lg hover:bg-slate-50 transition-colors bg-white shadow-sm group ${isOverdue ? 'border-red-200 bg-red-50/50' : 'border-slate-200'}`}>
        <div className="pt-1">
            <button
                onClick={() => markTaskDone(task.task_id)}
                className="w-6 h-6 rounded-full border-2 border-slate-300 text-transparent hover:border-green-500 hover:text-green-500 flex items-center justify-center transition-all group-hover:scale-110"
                title="Mark Complete"
            >
                ✔
            </button>
        </div>
        <div className="flex-1">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="font-bold text-slate-800 text-lg">{task.notes}</h3>
                    {task.source === 'auto' && <span className="text-[10px] bg-purple-100 text-purple-700 px-1 rounded ml-2">✨ Auto</span>}
                </div>
                <span className={`text-xs px-2 py-1 rounded font-bold uppercase ${task.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-500'}`}>
                    {task.priority || 'Normal'}
                </span>
            </div>
            <div className="text-sm text-slate-500 mt-1 flex gap-4 items-center">
                <span className={`${isOverdue ? 'text-red-600 font-bold' : ''}`}>
                    🗓 {new Date(task.due_at).toLocaleDateString()}
                    {task.due_at && new Date(task.due_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-blue-600 font-bold">{task.place_name}</span>
                {task.phone && <span>📞 {task.phone}</span>}
            </div>
            {task.lead_status && (
                <div className="mt-2 inline-block px-2 py-0.5 bg-slate-100 text-slate-800 text-xs rounded border border-slate-200">
                    Status: {task.lead_status}
                </div>
            )}
        </div>
    </div>
);

export default TaskCard;
