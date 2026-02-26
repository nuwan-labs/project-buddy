import { Link } from "react-router-dom"
import Layout from "@/components/Layout"

export default function NotFound() {
  return (
    <Layout>
      <div className="p-6 text-center mt-16">
        <h1 className="text-5xl font-bold text-gray-200">404</h1>
        <p className="text-muted-foreground mt-2">Page not found.</p>
        <Link to="/" className="text-blue-600 text-sm mt-3 inline-block hover:underline">
          ← Back to Dashboard
        </Link>
      </div>
    </Layout>
  )
}
