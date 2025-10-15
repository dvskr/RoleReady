import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to Role Ready
          </h1>
          <p className="text-lg text-gray-600">
            Upload your documents and get AI-powered insights
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Upload Documents
            </h2>
            <p className="text-gray-600 mb-4">
              Upload your resume, job descriptions, or other documents to get
              personalized insights and recommendations.
            </p>
            <Link
              href="/dashboard/upload"
              className="inline-block bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Start Uploading
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              API Status
            </h2>
            <p className="text-gray-600 mb-4">
              Check if the backend API is running and accessible.
            </p>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"
            >
              View API Docs
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
