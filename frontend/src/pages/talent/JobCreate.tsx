import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Briefcase, X } from 'lucide-react';


export default function JobCreate() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [skillsInput, setSkillsInput] = useState('');
  const [skillsList, setSkillsList] = useState<string[]>([]);
  const [minExp, setMinExp] = useState<number>(2.0);
  const [qualification, setQualification] = useState('B.E / B.Tech / MCA');
  const [location, setLocation] = useState('Coimbatore');
  const [employmentType, setEmploymentType] = useState('Full Time');
  const [status, setStatus] = useState('Open');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddSkill = () => {
    if (!skillsInput.trim()) return;
    const added = skillsInput
      .split(',')
      .map(s => s.trim())
      .filter(s => s && !skillsList.includes(s));
    setSkillsList([...skillsList, ...added]);
    setSkillsInput('');
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkillsList(skillsList.filter(s => s !== skillToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Job Title is required.');
      return;
    }
    if (!description.trim()) {
      setError('Job Description is required.');
      return;
    }

    // Merge any leftover text in skillsInput
    let finalSkills = [...skillsList];
    if (skillsInput.trim()) {
      const added = skillsInput
        .split(',')
        .map(s => s.trim())
        .filter(s => s && !finalSkills.includes(s));
      finalSkills = [...finalSkills, ...added];
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await axios.post('http://localhost:8000/api/v1/recruitment/jobs', {
        title,
        description,
        required_skills: finalSkills,
        minimum_experience: Number(minExp),
        qualification,
        location,
        employment_type: employmentType,
        status
      });

      navigate('/dashboard/talent/jobs');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to create job posting.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/dashboard/talent/jobs')}
          className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mb-3 gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Jobs
        </button>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Briefcase className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
          Create New Job
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Define position requirements and skills to enable automated resume matching.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
          {error}
        </div>
      )}

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-8 space-y-6">
        {/* Job Title */}
        <div>
          <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
            Job Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. Backend Developer"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>

        {/* Job Description */}
        <div>
          <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
            Job Description <span className="text-red-500">*</span>
          </label>
          <textarea
            rows={4}
            placeholder="Build and maintain high-performance backend microservices using FastAPI and MongoDB..."
            value={description}
            onChange={e => setDescription(e.target.value)}
            required
            className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>

        {/* Required Skills */}
        <div>
          <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
            Required Skills
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. Python, FastAPI, SQL (press Enter or Add)"
              value={skillsInput}
              onChange={e => setSkillsInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddSkill();
                }
              }}
              className="flex-1 px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={handleAddSkill}
              className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg text-sm font-medium"
            >
              Add
            </button>
          </div>
          {skillsList.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {skillsList.map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 text-xs font-medium rounded-full"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="hover:text-indigo-900 dark:hover:text-indigo-100"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Grid fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Minimum Experience */}
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
              Minimum Experience (Years)
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              value={minExp}
              onChange={e => setMinExp(parseFloat(e.target.value) || 0)}
              className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          {/* Qualification */}
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
              Qualification
            </label>
            <input
              type="text"
              placeholder="e.g. B.E / B.Tech / MCA"
              value={qualification}
              onChange={e => setQualification(e.target.value)}
              className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
              Location
            </label>
            <input
              type="text"
              placeholder="e.g. Coimbatore"
              value={location}
              onChange={e => setLocation(e.target.value)}
              className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          {/* Employment Type */}
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
              Employment Type
            </label>
            <select
              value={employmentType}
              onChange={e => setEmploymentType(e.target.value)}
              className="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="Full Time">Full Time</option>
              <option value="Part Time">Part Time</option>
              <option value="Contract">Contract</option>
              <option value="Remote">Remote</option>
              <option value="Internship">Internship</option>
            </select>
          </div>
        </div>

        {/* Status */}
        <div>
          <label className="block text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
            Status
          </label>
          <select
            value={status}
            onChange={e => setStatus(e.target.value)}
            className="w-full md:w-1/2 px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            <option value="Open">Open</option>
            <option value="Closed">Closed</option>
            <option value="Draft">Draft</option>
          </select>
        </div>

        {/* Buttons */}
        <div className="pt-6 border-t border-gray-100 dark:border-gray-700 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/dashboard/talent/jobs')}
            className="px-5 py-2.5 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm font-semibold rounded-lg"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm disabled:opacity-50 inline-flex items-center gap-2"
          >
            {isSubmitting ? 'Creating Job...' : 'Create Job'}
          </button>
        </div>
      </form>
    </div>
  );
}
