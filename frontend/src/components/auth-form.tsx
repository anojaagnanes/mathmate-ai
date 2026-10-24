'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowRight, Sparkles } from 'lucide-react';
import { post, setToken } from '@/lib/api';
import { Button } from './ui/button';
export function AuthForm({register: registering}: {register: boolean}) {
  const router = useRouter(); const [error, setError] = useState('');
  const schema = z.object({name: registering ? z.string().trim().min(1, 'Enter your name.').max(80) : z.string(), email: z.email('Enter a valid email.'), password: z.string().min(registering ? 10 : 1, 'Use at least 10 characters.').max(128)});
  const {register, handleSubmit, formState: {errors, isSubmitting}} = useForm<z.infer<typeof schema>>({resolver: zodResolver(schema), defaultValues: {name: '', email: '', password: ''}});
  return <main className="auth-page"><Link href="/" className="brand"><span className="brand-icon">m✦</span>MathMate AI</Link><div className="auth-card"><span className="icon-tile"><Sparkles/></span><span className="eyebrow">YOUR NEXT CHAPTER STARTS HERE</span><h1>{registering ? 'Hello, possibility.' : 'Welcome back.'}</h1><p>{registering ? 'A little practice today. A little more confidence tomorrow.' : 'Let’s pick up where your curiosity left off.'}</p><form onSubmit={handleSubmit(async values => {setError(''); try {const result = await post<{access_token: string}>(registering ? '/auth/register' : '/auth/login', values); setToken(result.access_token); router.push('/app');} catch (e) {setError((e as Error).message);}})}>{registering && <label>Your name<input autoComplete="name" {...register('name')}/><small className="error">{errors.name?.message}</small></label>}<label>Email address<input type="email" autoComplete="email" {...register('email')}/><small className="error">{errors.email?.message}</small></label><label>Password<input type="password" autoComplete={registering ? 'new-password' : 'current-password'} {...register('password')}/><small className="error">{errors.password?.message}</small></label>{error && <p role="alert" className="error-box">{error}</p>}<Button disabled={isSubmitting}>{isSubmitting ? 'One moment…' : registering ? 'Create my account' : 'Continue learning'}<ArrowRight size={17}/></Button></form><p className="auth-switch">{registering ? 'Already part of MathMate?' : 'New to MathMate?'} <Link href={registering ? '/login' : '/register'}>{registering ? 'Log in' : 'Create an account'}</Link></p></div></main>;
}
