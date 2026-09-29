import React from 'react';
import { CheckCircle2, Info } from 'lucide-react';
interface ToastProps { message: string; isVisible: boolean; type?: 'success' | 'info'; }
export const Toast: React.FC<ToastProps> = ({ message, isVisible, type = 'success' }) => !isVisible ? null : <div className="toast"><span className="toast-icon">{type === 'success' ? <CheckCircle2 size={16} /> : <Info size={16} />}</span><span>{message}</span></div>;
