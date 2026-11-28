import { useEffect, useState } from 'react'

type Notification = {
  id: number
  title: string
  severity: string
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function NotificationList() {
  const [notifications, setNotifications] = useState<Notification[]>([])

  useEffect(() => {
    fetch(`${API_URL}/api/notifications?page=1&page_size=20`)
      .then((response) => response.json())
      .then((value: { items: Notification[] }) => setNotifications(value.items))
  }, [])

  return (
    <article className="panel">
      <h2>Notifications</h2>
      {notifications.map((notification) => (
        <div className="row" key={notification.id}>
          <span>{notification.title}</span>
          <b>{notification.severity}</b>
        </div>
      ))}
    </article>
  )
}

export default NotificationList
