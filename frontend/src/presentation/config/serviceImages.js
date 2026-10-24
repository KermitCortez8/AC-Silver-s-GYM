import { useAppResources } from '../../application/services/appResources.js';

export const useServiceImages = () => {
  const { landingImageUrl } = useAppResources();
  return Object.fromEntries(['fitness', 'musculacion', 'cardio', 'baile'].map(service =>
    [service, landingImageUrl(`service-${service}.jpg`)]));
};
